# -*- coding: utf-8 -*-
import base64
import json
import logging
import urllib.request
import urllib.error
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    ai_extraction_status = fields.Selection([
        ('none', 'Nevyťažené'),
        ('in_progress', 'Spracováva sa...'),
        ('done', 'Úspešne vyťažené cez AI'),
        ('failed', 'Chyba vyťaženia'),
    ], string="AI Vyťaženie", default='none', readonly=True, copy=False)

    def action_ai_extract_invoice(self):
        """Spustí AI vyťaženie faktúry z pripojenej PDF prílohy."""
        self.ensure_one()

        if self.state != 'draft':
            raise UserError(_("AI vyťaženie je možné spustiť iba na konceptoch (Draft) faktúr."))

        # 1. Nájdenie PDF prílohy
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'account.move'),
            ('res_id', '=', self.id),
            ('mimetype', '=', 'application/pdf')
        ], order='id desc', limit=1)

        if not attachments:
            # Skús nájsť akúkoľvek PDF prílohu v chate
            attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'account.move'),
                ('res_id', '=', self.id),
            ], order='id desc', limit=1)

        if not attachments:
            raise UserError(_("Nenašla sa žiadna PDF príloha faktúry. Najskôr prosím priložte PDF súbor faktúry do príloh alebo chatu."))

        # 2. Načítanie nastavení
        ICP = self.env['ir.config_parameter'].sudo()
        provider = ICP.get_param('ai_invoice_extractor.provider', 'gemini')
        api_key = ICP.get_param('ai_invoice_extractor.api_key', '').strip()
        auto_create_partner = ICP.get_param('ai_invoice_extractor.auto_create_partner', 'True') == 'True'

        if not api_key:
            raise UserError(_("Nie je nastavený AI API kľúč. Nastavte ho v Fakturácia -> Konfigurácia -> Nastavenia -> AI Invoice Extractor."))

        self.ai_extraction_status = 'in_progress'

        try:
            pdf_bytes = base64.b64decode(attachments.datas)
            extracted_data = self._call_ai_api(pdf_bytes, provider, api_key)
            self._apply_extracted_data(extracted_data, auto_create_partner)
            self.ai_extraction_status = 'done'

            self.message_post(
                body=_("<b>AI Vyťaženie úspešné:</b> Dodávateľ: %s, Číslo: %s, Dátum: %s, Celková suma: %s") % (
                    extracted_data.get('supplier_name', 'Neznámy'),
                    extracted_data.get('invoice_number', '-'),
                    extracted_data.get('invoice_date', '-'),
                    extracted_data.get('total_amount', '-')
                )
            )
        except Exception as e:
            self.ai_extraction_status = 'failed'
            _logger.exception("Chyba pri AI vyťažovaní faktúry")
            raise UserError(_("Chyba pri AI vyťažení: %s") % str(e))

        return True

    def _call_ai_api(self, pdf_bytes, provider, api_key):
        """Zavolá príslušné AI API a vráti štruktúrovaný JSON."""
        prompt = """
        You are an expert accountant OCR assistant. Analyze this invoice/bill document and return a pure, strictly valid JSON object without markdown fences, with these exact keys:
        {
            "supplier_name": "Company Name",
            "supplier_vat": "SK... or CZ... or other VAT ID",
            "supplier_ico": "Company registration number / ICO",
            "invoice_number": "Invoice reference number (variabilny symbol / cislo faktury)",
            "invoice_date": "YYYY-MM-DD",
            "due_date": "YYYY-MM-DD",
            "currency": "EUR",
            "total_amount": 123.45,
            "items": [
                {
                    "description": "Item description",
                    "quantity": 1.0,
                    "unit_price": 50.0,
                    "tax_percent": 20
                }
            ]
        }
        """

        if provider == 'gemini':
            # Google Gemini REST API volanie
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": "application/pdf",
                                    "data": base64.b64encode(pdf_bytes).decode('utf-8')
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "response_mime_type": "application/json"
                }
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                res_json = json.loads(resp.read().decode('utf-8'))
                raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
                return json.loads(raw_text)

        elif provider == 'openai':
            # OpenAI API volanie (GPT-4o mini s podporou document/vision alebo text)
            url = "https://api.openai.com/v1/chat/completions"
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a professional invoice parsing assistant. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"}
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}'
                }
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                res_json = json.loads(resp.read().decode('utf-8'))
                raw_text = res_json['choices'][0]['message']['content']
                return json.loads(raw_text)

        else:
            raise UserError(_("Neznámy alebo nepodporovaný poskytovateľ AI: %s") % provider)

    def _apply_extracted_data(self, data, auto_create_partner):
        """Aplikuje vyťažené dáta do polí Odoo faktúry."""
        vals = {}

        # 1. Partner
        partner = False
        vat = data.get('supplier_vat')
        ico = data.get('supplier_ico')
        name = data.get('supplier_name')

        if vat:
            partner = self.env['res.partner'].search([('vat', '=', vat)], limit=1)
        if not partner and ico:
            partner = self.env['res.partner'].search(['|', ('ref', '=', ico), ('company_registry', '=', ico)], limit=1)
        if not partner and name:
            partner = self.env['res.partner'].search([('name', 'ilike', name)], limit=1)

        if not partner and auto_create_partner and name:
            partner_vals = {
                'name': name,
                'is_company': True,
                'supplier_rank': 1,
            }
            if vat:
                partner_vals['vat'] = vat
            if ico:
                partner_vals['ref'] = ico
            partner = self.env['res.partner'].create(partner_vals)

        if partner:
            vals['partner_id'] = partner.id

        # 2. Číslo a dátumy
        if data.get('invoice_number'):
            vals['ref'] = str(data['invoice_number'])
        if data.get('invoice_date'):
            vals['invoice_date'] = data['invoice_date']
        if data.get('due_date'):
            vals['invoice_date_due'] = data['due_date']

        self.write(vals)

        # 3. Položky faktúry (Lines)
        items = data.get('items', [])
        if items and self.invoice_line_ids:
            # Vymažeme prázdne default riadky ak sú
            self.invoice_line_ids.unlink()

        line_commands = []
        for item in items:
            line_vals = {
                'name': item.get('description', 'Položka faktúry'),
                'quantity': float(item.get('quantity', 1.0)),
                'price_unit': float(item.get('unit_price', 0.0)),
            }
            line_commands.append((0, 0, line_vals))

        if line_commands:
            self.write({'invoice_line_ids': line_commands})
