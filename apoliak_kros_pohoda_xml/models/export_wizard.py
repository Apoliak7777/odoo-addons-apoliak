# -*- coding: utf-8 -*-
import base64
import datetime
import re
import xml.etree.ElementTree as ET
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ApoliakAccountingExportWizard(models.TransientModel):
    _name = 'apoliak.accounting.export.wizard'
    _description = 'Export Faktúr do KROS Omega a Stormware Pohoda XML'

    export_system = fields.Selection([
        ('pohoda', 'Stormware POHODA (XML v2.0 dataPack)'),
        ('omega', 'KROS OMEGA (Výmenný formát TXT / XML)'),
    ], string="Cieľový účtovný program", default='pohoda', required=True)

    date_from = fields.Date(
        string="Dátum od",
        required=True,
        default=lambda self: fields.Date.today().replace(day=1))
    date_to = fields.Date(
        string="Dátum do",
        required=True,
        default=fields.Date.today)
    move_types = fields.Selection([
        ('both', 'Vydané aj prijaté faktúry'),
        ('out', 'Iba vydané faktúry (Odberateľské)'),
        ('in', 'Iba prijaté faktúry (Dodávateľské)'),
    ], string="Typ dokladov", default='both', required=True)

    exported_file = fields.Binary(string="Exportovaný súbor", readonly=True)
    exported_filename = fields.Char(string="Názov súboru", readonly=True)
    export_count = fields.Integer(string="Počet vyexportovaných dokladov", readonly=True)

    def action_generate_export(self):
        self.ensure_one()
        domain = [
            ('state', '=', 'posted'),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
        ]
        if self.move_types == 'out':
            domain.append(('move_type', 'in', ('out_invoice', 'out_refund')))
        elif self.move_types == 'in':
            domain.append(('move_type', 'in', ('in_invoice', 'in_refund')))
        else:
            domain.append(('move_type', 'in', ('out_invoice', 'out_refund', 'in_invoice', 'in_refund')))

        moves = self.env['account.move'].search(domain, order='invoice_date asc, id asc')
        if not moves:
            raise UserError(_("V zvolenom období sa nenašli žiadne zaúčtované faktúry."))

        if self.export_system == 'pohoda':
            content_bytes = self._build_pohoda_xml(moves)
            filename = f"pohoda_export_{self.date_from}_{self.date_to}.xml"
        else:
            content_bytes = self._build_kros_omega_txt(moves)
            filename = f"omega_export_{self.date_from}_{self.date_to}.txt"

        self.write({
            'exported_file': base64.b64encode(content_bytes),
            'exported_filename': filename,
            'export_count': len(moves),
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'apoliak.accounting.export.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def _build_pohoda_xml(self, moves):
        """Generuje platný Stormware Pohoda XML dataPack v2.0."""
        company_ico = (self.env.company.company_registry or self.env.company.vat or '00000000')
        company_ico_digits = ''.join(re.findall(r'\d+', company_ico))[:8] or '00000000'

        root = ET.Element('dat:dataPack', {
            'id': f"ODOO-{datetime.date.today().strftime('%Y%m%d')}",
            'ico': company_ico_digits,
            'application': 'ApoliakOdooBridge',
            'version': '2.0',
            'note': 'Export z Odoo ERP',
            'xmlns:dat': 'http://www.stormware.cz/schema/version_2/data.xsd',
            'xmlns:inv': 'http://www.stormware.cz/schema/version_2/invoice.xsd',
            'xmlns:typ': 'http://www.stormware.cz/schema/version_2/type.xsd',
        })

        for move in moves:
            item_pack = ET.SubElement(root, 'dat:dataPackItem', {
                'id': move.name or str(move.id),
                'version': '2.0'
            })
            inv_el = ET.SubElement(item_pack, 'inv:invoice', {'version': '2.0'})
            header = ET.SubElement(inv_el, 'inv:invoiceHeader')

            inv_type = 'issuedInvoice' if move.move_type in ('out_invoice', 'out_refund') else 'receivedInvoice'
            ET.SubElement(header, 'inv:invoiceType').text = inv_type

            num_el = ET.SubElement(header, 'inv:number')
            ET.SubElement(num_el, 'typ:numberRequested').text = move.name or ''

            vs_raw = move.payment_reference or move.ref or move.name or ''
            ET.SubElement(header, 'inv:symVar').text = ''.join(re.findall(r'\d+', vs_raw))[:20]
            ET.SubElement(header, 'inv:date').text = str(move.invoice_date or '')
            ET.SubElement(header, 'inv:dateDue').text = str(move.invoice_date_due or move.invoice_date or '')
            ET.SubElement(header, 'inv:text').text = f"Faktura {move.name or ''}"

            partner = move.partner_id
            if partner:
                p_ident = ET.SubElement(header, 'inv:partnerIdentity')
                addr = ET.SubElement(p_ident, 'typ:address')
                ET.SubElement(addr, 'typ:company').text = partner.name or ''
                ET.SubElement(addr, 'typ:street').text = partner.street or ''
                ET.SubElement(addr, 'typ:city').text = partner.city or ''
                ET.SubElement(addr, 'typ:zip').text = partner.zip or ''
                if partner.company_registry:
                    ET.SubElement(addr, 'typ:ico').text = partner.company_registry
                if partner.vat:
                    ET.SubElement(addr, 'typ:dic').text = partner.vat

            detail = ET.SubElement(inv_el, 'inv:invoiceDetail')
            for line in move.invoice_line_ids.filtered(lambda l: l.display_type == 'product' or not l.display_type):
                item = ET.SubElement(detail, 'inv:invoiceItem')
                ET.SubElement(item, 'inv:text').text = (line.name or 'Polozka')[:90]
                ET.SubElement(item, 'inv:quantity').text = f"{line.quantity:.2f}"
                ET.SubElement(item, 'inv:payVAT').text = 'false'
                ET.SubElement(item, 'inv:rateVAT').text = 'high' if line.tax_ids else 'none'
                hc = ET.SubElement(item, 'inv:homeCurrency')
                ET.SubElement(hc, 'typ:unitPrice').text = f"{line.price_unit:.2f}"
                ET.SubElement(hc, 'typ:price').text = f"{line.price_subtotal:.2f}"
                ET.SubElement(hc, 'typ:priceVAT').text = f"{(line.price_total - line.price_subtotal):.2f}"

            summary = ET.SubElement(inv_el, 'inv:invoiceSummary')
            sum_hc = ET.SubElement(summary, 'inv:homeCurrency')
            ET.SubElement(sum_hc, 'typ:priceNone').text = '0.00'
            ET.SubElement(sum_hc, 'typ:priceHigh').text = f"{move.amount_untaxed:.2f}"
            ET.SubElement(sum_hc, 'typ:priceHighVAT').text = f"{move.amount_tax:.2f}"
            ET.SubElement(sum_hc, 'typ:priceHighSum').text = f"{move.amount_total:.2f}"

        xml_str = ET.tostring(root, encoding='utf-8', xml_declaration=True)
        return xml_str

    def _build_kros_omega_txt(self, moves):
        """Generuje KROS Omega výmenný formát (R00, R01, R02)."""
        lines = ["R00\tT00\tOdoo ERP Export pre KROS Omega"]
        for move in moves:
            partner = move.partner_id
            doc_type = "OF" if move.move_type in ('out_invoice', 'out_refund') else "DF"
            vs = ''.join(re.findall(r'\d+', move.payment_reference or move.name or ''))[:10]
            ico = (partner.company_registry or '').replace(' ', '')
            dic = (partner.vat or '').replace(' ', '')
            r01 = "\t".join([
                "R01",
                doc_type,
                move.name or "",
                vs,
                str(move.invoice_date or ""),
                str(move.invoice_date_due or move.invoice_date or ""),
                f"{move.amount_total:.2f}",
                move.currency_id.name or "EUR",
                (partner.name or "")[:60],
                ico,
                dic,
                (partner.street or "")[:40],
                (partner.city or "")[:30],
                (partner.zip or "")[:10],
            ])
            lines.append(r01)

            for line in move.invoice_line_ids.filtered(lambda l: l.display_type == 'product' or not l.display_type):
                tax_rate = line.tax_ids[0].amount if line.tax_ids else 0.0
                r02 = "\t".join([
                    "R02",
                    (line.name or "Polozka").replace("\t", " ").replace("\n", " ")[:60],
                    f"{line.quantity:.2f}",
                    f"{line.price_unit:.2f}",
                    f"{line.price_subtotal:.2f}",
                    f"{tax_rate:.0f}",
                    f"{(line.price_total - line.price_subtotal):.2f}",
                    f"{line.price_total:.2f}",
                ])
                lines.append(r02)

        return ("\r\n".join(lines) + "\r\n").encode("utf-8")
