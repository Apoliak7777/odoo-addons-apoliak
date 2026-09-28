# -*- coding: utf-8 -*-
import base64
import binascii
import io
import lzma
import re
import struct
import logging
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

BASE32HEX_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUV"


def _encode_base32hex(data: bytes) -> str:
    """Kóduje bajty do Base32hex (RFC 4648) podľa špecifikácie SBA Pay by Square."""
    bits = 0
    value = 0
    output = []
    for byte in data:
        value = (value << 8) | byte
        bits += 8
        while bits >= 5:
            output.append(BASE32HEX_ALPHABET[(value >> (bits - 5)) & 0x1F])
            bits -= 5
    if bits > 0:
        output.append(BASE32HEX_ALPHABET[(value << (5 - bits)) & 0x1F])
    return "".join(output)


def generate_pay_by_square_string(amount, currency, iban, bic, vs, ks, ss, due_date, note, beneficiary_name):
    """Vygeneruje oficiálny Pay by Square reťazec podľa štandardu Slovenskej bankovej asociácie (SBA)."""
    fields_tab = [
        "",  # Payment ID
        "1",  # Count of payments
        "1",  # Payment option (1 = paymentorder)
        f"{amount:.2f}",
        currency or "EUR",
        due_date or "",
        vs or "",
        ks or "",
        ss or "",
        "",  # Originators reference
        (note or "")[:140].replace("\t", " ").replace("\n", " "),
        "1",  # Bank accounts count
        (iban or "").replace(" ", ""),
        (bic or "").replace(" ", ""),
        "0",  # Standing order
        "0",  # Direct debit
        (beneficiary_name or "")[:70].replace("\t", " "),
        "",  # Beneficiary address 1
        "",  # Beneficiary address 2
    ]
    raw_tsv = "\t".join(fields_tab).encode("utf-8")
    crc = binascii.crc32(raw_tsv) & 0xFFFFFFFF
    payload_with_crc = struct.pack("<I", crc) + raw_tsv

    lzma_filters = [{
        "id": lzma.FILTER_LZMA1,
        "lc": 3,
        "lp": 0,
        "pb": 2,
        "dict_size": 128 * 1024,
    }]
    compressed = lzma.compress(payload_with_crc, format=lzma.FORMAT_RAW, filters=lzma_filters)
    header = b"\x00\x00" + struct.pack("<H", len(payload_with_crc))
    return _encode_base32hex(header + compressed)


def generate_cz_spd_string(amount, currency, iban, vs, due_date, note, beneficiary_name):
    """Vygeneruje český štandard QR Platba (SPD 1.0)."""
    iban_clean = (iban or "").replace(" ", "")
    parts = [
        "SPD*1.0",
        f"ACC:{iban_clean}",
        f"AM:{amount:.2f}",
        f"CC:{currency or 'CZK'}",
    ]
    if vs:
        parts.append(f"X-VS:{vs[:10]}")
    if due_date:
        parts.append(f"DT:{due_date}")
    if beneficiary_name:
        parts.append(f"RN:{beneficiary_name[:35].replace('*', '')}")
    if note:
        parts.append(f"MSG:{note[:60].replace('*', '')}")
    return "*".join(parts)


class AccountMove(models.Model):
    _inherit = 'account.move'

    apoliak_variable_symbol = fields.Char(
        string="Variabilný symbol (VS)",
        compute="_compute_apoliak_payment_qr",
        store=True,
        readonly=False,
        help="Číselný variabilný symbol pre párovanie platieb v SK a CZ bankách.")
    apoliak_qr_format = fields.Selection([
        ('pbs', 'Slovenský Pay by Square (SBA)'),
        ('spd', 'Česká QR Platba (SPD 1.0)'),
    ], string="Formát QR kódu", default='pbs', required=True)
    apoliak_qr_payload = fields.Char(
        string="QR Dátový reťazec",
        compute="_compute_apoliak_payment_qr",
        store=True)
    apoliak_qr_image = fields.Binary(
        string="QR Kód na úhradu",
        compute="_compute_apoliak_payment_qr",
        store=True,
        attachment=False)

    @api.depends('amount_residual', 'amount_total', 'currency_id', 'partner_bank_id', 'name', 'payment_reference', 'invoice_date_due', 'apoliak_qr_format', 'state')
    def _compute_apoliak_payment_qr(self):
        for move in self:
            raw_ref = move.payment_reference or move.name or ''
            digits = ''.join(re.findall(r'\d+', raw_ref))[-10:]
            if not move.apoliak_variable_symbol:
                move.apoliak_variable_symbol = digits

            vs = move.apoliak_variable_symbol or digits
            bank_acc = move.partner_bank_id or (move.company_id.partner_id.bank_ids[:1])
            iban = bank_acc.sanitized_acc_number or bank_acc.acc_number if bank_acc else ''
            bic = bank_acc.bank_id.bic if (bank_acc and bank_acc.bank_id) else ''
            amount = move.amount_residual if move.state == 'posted' and move.amount_residual > 0 else move.amount_total

            if not iban or amount <= 0 or move.move_type not in ('out_invoice', 'in_invoice'):
                move.apoliak_qr_payload = False
                move.apoliak_qr_image = False
                continue

            due_str = move.invoice_date_due.strftime('%Y%m%d') if move.invoice_date_due else ''
            currency_name = move.currency_id.name or 'EUR'
            note = f"Faktura {move.name or ''}".strip()
            beneficiary = move.company_id.name or ''

            try:
                if move.apoliak_qr_format == 'spd' or currency_name == 'CZK':
                    payload = generate_cz_spd_string(amount, currency_name, iban, vs, due_str, note, beneficiary)
                else:
                    payload = generate_pay_by_square_string(amount, currency_name, iban, bic, vs, "0308", "", due_str, note, beneficiary)

                move.apoliak_qr_payload = payload
                move.apoliak_qr_image = move._render_qr_png_base64(payload)
            except Exception as e:
                _logger.warning("Nepodarilo sa vygenerovať Pay by Square QR kód: %s", e)
                move.apoliak_qr_payload = False
                move.apoliak_qr_image = False

    def _render_qr_png_base64(self, payload):
        try:
            import qrcode
            qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=6, border=2)
            qr.add_data(payload)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return base64.b64encode(buf.getvalue())
        except Exception as e:
            _logger.debug("qrcode knižnica nedostupná: %s", e)
            return False
