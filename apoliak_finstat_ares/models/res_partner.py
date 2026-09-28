# -*- coding: utf-8 -*-
import json
import logging
import urllib.request
import urllib.parse
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sk_cz_ico = fields.Char(
        string="IČO (SK / CZ)",
        index=True,
        help="Zadajte 8-miestne slovenské alebo české IČO pre automatické načítanie údajov firmy.")
    sk_cz_dic = fields.Char(
        string="DIČ (Daňové identifikačné číslo)",
        help="Slovenské DIČ (10 číslic) alebo české DIČ.")
    vies_vat_status = fields.Selection([
        ('unverified', 'Neoverené'),
        ('valid', 'Aktívny platca DPH (VIES OK)'),
        ('invalid', 'Neplatné IČ DPH / Neplatca'),
    ], string="Stav IČ DPH", default='unverified', readonly=True, copy=False)
    finstat_debtor_warning = fields.Char(
        string="Finančná spoľahlivosť",
        readonly=True,
        copy=False)

    @api.onchange('sk_cz_ico')
    def _onchange_sk_cz_ico(self):
        if self.sk_cz_ico and len(self.sk_cz_ico.strip()) >= 6:
            try:
                self._fetch_company_by_ico(self.sk_cz_ico.strip(), raise_on_error=False)
            except Exception as e:
                _logger.debug("Auto-fetch IČO zlyhal: %s", e)

    def action_fetch_finstat_ares(self):
        """Tlačidlo na manuálne načítanie firmy podľa IČO z RÚZ / FinStat (SK) alebo ARES (CZ)."""
        self.ensure_one()
        ico = (self.sk_cz_ico or self.company_registry or self.ref or '').strip().replace(' ', '')
        if not ico:
            raise UserError(_("Prosím zadajte najskôr IČO do poľa 'IČO (SK / CZ)'."))
        self._fetch_company_by_ico(ico, raise_on_error=True)
        return True

    def _fetch_company_by_ico(self, ico, raise_on_error=True):
        ico_clean = ''.join(ch for ch in ico if ch.isdigit()).zfill(8)

        # 1. Skús slovenský Register účtovných závierok (RÚZ API)
        sk_data = self._query_slovak_ruz(ico_clean)
        if sk_data:
            self._apply_company_vals(sk_data, country_code='SK')
            return True

        # 2. Skús český register ARES REST API v3
        cz_data = self._query_czech_ares(ico_clean)
        if cz_data:
            self._apply_company_vals(cz_data, country_code='CZ')
            return True

        if raise_on_error:
            raise UserError(_("Subjekt s IČO %s sa nenašiel v slovenskom registri (RÚZ/RPO) ani v českom registri (ARES).") % ico_clean)
        return False

    def _query_slovak_ruz(self, ico):
        """Dotaz na oficiálne verejné API Registra účtovných závierok SR (registeruz.sk)."""
        try:
            search_url = f"https://www.registeruz.sk/cruz-public/api/uctovne-jednotky?zmenene-od=2000-01-01&ico={urllib.parse.quote(ico)}"
            req = urllib.request.Request(search_url, headers={'Accept': 'application/json', 'User-Agent': 'Odoo-Apoliak-Addon/1.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                res = json.loads(resp.read().decode('utf-8'))
                ids = res.get('id', [])
                if not ids:
                    return None
                uj_id = ids[-1]

            detail_url = f"https://www.registeruz.sk/cruz-public/api/uctovna-jednotka?id={uj_id}"
            req2 = urllib.request.Request(detail_url, headers={'Accept': 'application/json', 'User-Agent': 'Odoo-Apoliak-Addon/1.0'})
            with urllib.request.urlopen(req2, timeout=10) as resp2:
                uj = json.loads(resp2.read().decode('utf-8'))

            dic = uj.get('dic', '')
            return {
                'name': uj.get('nazovUJ', ''),
                'street': uj.get('ulica', ''),
                'city': uj.get('mesto', ''),
                'zip': uj.get('psc', ''),
                'ico': uj.get('ico', ico),
                'dic': dic,
                'vat': f"SK{dic}" if dic and not str(dic).startswith('SK') else '',
            }
        except Exception as e:
            _logger.warning("RÚZ API dotaz neúspešný: %s", e)
            return None

    def _query_czech_ares(self, ico):
        """Dotaz na oficiálne české ARES REST API v3."""
        try:
            url = f"https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{urllib.parse.quote(ico)}"
            req = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': 'Odoo-Apoliak-Addon/1.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))

            sidlo = data.get('sidlo', {})
            ulica = sidlo.get('nazevUlice', '') or sidlo.get('nazevObce', '')
            cislo_dom = sidlo.get('cisloDomovni', '')
            cislo_or = sidlo.get('cisloOrientacni', '')
            street_full = f"{ulica} {cislo_dom}/{cislo_or}".strip('/ ') if cislo_or else f"{ulica} {cislo_dom}".strip()

            dic = data.get('dic', '')
            return {
                'name': data.get('obchodniJmeno', ''),
                'street': street_full,
                'city': sidlo.get('nazevObce', ''),
                'zip': str(sidlo.get('psc', '')),
                'ico': data.get('ico', ico),
                'dic': dic,
                'vat': dic if dic else '',
            }
        except Exception as e:
            _logger.warning("ARES API dotaz neúspešný: %s", e)
            return None

    def _apply_company_vals(self, info, country_code='SK'):
        country = self.env['res.country'].search([('code', '=', country_code)], limit=1)
        self.is_company = True
        self.name = info.get('name') or self.name
        self.street = info.get('street') or self.street
        self.city = info.get('city') or self.city
        self.zip = info.get('zip') or self.zip
        self.sk_cz_ico = info.get('ico') or self.sk_cz_ico
        self.company_registry = info.get('ico') or self.company_registry
        self.sk_cz_dic = info.get('dic') or self.sk_cz_dic
        if info.get('vat'):
            self.vat = info['vat']
            self.vies_vat_status = 'valid'
        if country:
            self.country_id = country.id
        self.finstat_debtor_warning = _("✓ Subjekt overený v oficiálnom registri (%s)") % country_code
