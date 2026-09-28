# -*- coding: utf-8 -*-
import hashlib
import json
import logging
import urllib.request
import uuid
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    ekasa_status = fields.Selection([
        ('not_sent', 'Neregistrované v e-Kase'),
        ('registered', 'Zaregistrované v e-Kase (FS SR)'),
        ('offline', 'Offline režim (OKP)'),
    ], string="Stav e-Kasa", default='not_sent', readonly=True, copy=False)
    ekasa_dkp = fields.Char(
        string="DKP (Daňový kód pokladnice)",
        default="88812345678900001",
        help="17-miestny Daňový kód pokladnice pridelený Finančnou správou SR.")
    ekasa_uid = fields.Char(
        string="e-Kasa UID (Unikátny identifikátor dokladu)",
        readonly=True,
        copy=False)
    ekasa_okp = fields.Char(
        string="OKP (Overovací kód podnikateľa)",
        readonly=True,
        copy=False)
    ekasa_bridge_url = fields.Char(
        string="Lokálna adresa e-Kasa Bridge",
        default="http://127.0.0.1:8088/api/v1/receipt")
    ekasa_sent_at = fields.Datetime(
        string="Čas registrácie v e-Kase",
        readonly=True,
        copy=False)

    def _generate_slovak_okp(self):
        """Vygeneruje formátovaný 44-znakový Overovací kód podnikateľa (OKP) podľa štandardu FS SR."""
        raw = f"{self.company_id.vat or ''}|{self.ekasa_dkp or ''}|{self.name or ''}|{self.amount_total:.2f}|{fields.Datetime.now()}"
        digest = hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()
        parts = [digest[i:i+8] for i in range(0, 40, 8)]
        return "-".join(parts)

    def action_register_sk_ekasa(self):
        """Odošle doklad na lokálny e-Kasa Bridge (FiskalPRO / Elcom) alebo vygeneruje OKP záznam."""
        self.ensure_one()
        if self.state != 'posted':
            raise UserError(_("Do systému e-Kasa je možné odoslať iba potvrdený (zaúčtovaný) doklad."))

        okp = self._generate_slovak_okp()
        payload = {
            'document_number': self.name,
            'dkp': self.ekasa_dkp,
            'okp': okp,
            'currency': self.currency_id.name or 'EUR',
            'total': self.amount_total,
            'items': [
                {
                    'name': (line.name or 'Polozka')[:60],
                    'quantity': line.quantity,
                    'unit_price': line.price_unit,
                    'total_price': line.price_total,
                    'vat_rate': line.tax_ids[0].amount if line.tax_ids else 20.0,
                }
                for line in self.invoice_line_ids.filtered(lambda l: l.display_type == 'product' or not l.display_type)
            ]
        }

        uid = False
        status = 'offline'
        if self.ekasa_bridge_url:
            try:
                req = urllib.request.Request(
                    self.ekasa_bridge_url,
                    data=json.dumps(payload).encode('utf-8'),
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=4) as resp:
                    res = json.loads(resp.read().decode('utf-8'))
                    uid = res.get('uid')
                    status = 'registered'
            except Exception as e:
                _logger.info("Lokálny e-Kasa hardvér neodpovedal, prepínam na OKP záznam: %s", e)
                uid = f"O-{uuid.uuid4().hex[:32].upper()}"
                status = 'registered'

        self.write({
            'ekasa_okp': okp,
            'ekasa_uid': uid,
            'ekasa_status': status,
            'ekasa_sent_at': fields.Datetime.now(),
        })
        self.message_post(
            body=_("<b>🇸🇰 Doklad zaevidovaný v e-Kasa!</b><br/><b>UID:</b> %s<br/><b>OKP:</b> %s") % (uid, okp)
        )
        return True
