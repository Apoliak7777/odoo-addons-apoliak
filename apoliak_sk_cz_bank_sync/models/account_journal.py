# -*- coding: utf-8 -*-
import datetime
import json
import logging
import re
import urllib.request
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    apoliak_bank_sync_provider = fields.Selection([
        ('none', 'Manuálne / Vypnuté'),
        ('fio', 'Fio banka API (SK / CZ)'),
        ('camt053', 'Tatra banka / SLSP / VÚB / ČSOB (CAMT.053 + VS párovanie)'),
    ], string="SK/CZ Banková synchronizácia", default='none')

    apoliak_fio_api_token = fields.Char(
        string="Fio API Token (64 znakov)",
        help="Read-only API token vygenerovaný v Internetbankingu Fio banky.")
    apoliak_last_sync_date = fields.Datetime(
        string="Posledná synchronizácia",
        readonly=True)

    def action_sync_sk_cz_bank(self):
        """Stiahne nové transakcie z Fio API a spáruje podľa Variabilného symbolu."""
        self.ensure_one()
        if self.type != 'bank':
            raise UserError(_("Synchronizáciu je možné spustiť iba na bankovom denníku."))

        if self.apoliak_bank_sync_provider != 'fio' or not self.apoliak_fio_api_token:
            raise UserError(_("Prosím nastavte v denníku poskytovateľa 'Fio banka API' a vložte 64-znakový Fio API Token."))

        token = self.apoliak_fio_api_token.strip()
        date_to = datetime.date.today().strftime('%Y-%m-%d')
        date_from = (datetime.date.today() - datetime.timedelta(days=14)).strftime('%Y-%m-%d')
        url = f"https://fioapi.fio.cz/v1/rest/periods/{token}/{date_from}/{date_to}/transactions.json"

        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Odoo-Apoliak-BankSync/1.0'})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            raise UserError(_("Chyba pri sťahovaní z Fio API: %s") % str(e))

        stmt_data = data.get('accountStatement', {})
        tx_list = stmt_data.get('transactionList', {}).get('transaction', [])
        imported_count = 0

        for tx in tx_list:
            tx_id = str((tx.get('column22') or {}).get('value', ''))
            date_str = str((tx.get('column0') or {}).get('value', ''))[:10]
            amount = float((tx.get('column1') or {}).get('value', 0.0))
            vs = str((tx.get('column5') or {}).get('value', '')).strip()
            partner_name = (tx.get('column10') or {}).get('value') or (tx.get('column7') or {}).get('value') or 'Banková transakcia'
            msg = (tx.get('column16') or {}).get('value') or ''

            if not tx_id:
                continue

            existing = self.env['account.bank.statement.line'].search([
                ('journal_id', '=', self.id),
                ('unique_import_id', '=', f"FIO-{tx_id}")
            ], limit=1)
            if existing:
                continue

            # Pokus o nájdenie faktúry a partnera podľa VS
            partner_id = False
            payment_ref = f"{partner_name} (VS: {vs})" if vs else partner_name
            if vs:
                matched_move = self.env['account.move'].search([
                    ('state', '=', 'posted'),
                    '|', ('payment_reference', 'ilike', vs), ('name', 'ilike', vs)
                ], limit=1)
                if matched_move and matched_move.partner_id:
                    partner_id = matched_move.partner_id.id
                    payment_ref = f"VS:{vs} - {matched_move.name} ({msg})".strip()

            self.env['account.bank.statement.line'].create({
                'journal_id': self.id,
                'date': date_str or fields.Date.today(),
                'payment_ref': payment_ref,
                'partner_id': partner_id,
                'amount': amount,
                'unique_import_id': f"FIO-{tx_id}",
            })
            imported_count += 1

        self.apoliak_last_sync_date = fields.Datetime.now()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Banková synchronizácia dokončená'),
                'message': _('Úspešne naimportovaných %s nových pohybov s párovaním VS.') % imported_count,
                'sticky': False,
                'type': 'success',
            }
        }
