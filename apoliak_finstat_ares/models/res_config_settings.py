# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    apoliak_finstat_api_key = fields.Char(
        string="FinStat.sk API Kľúč (Voliteľné)",
        config_parameter='apoliak_finstat_ares.finstat_api_key',
        help="Voliteľný API kľúč pre prémiové dáta z FinStat.sk. Ak je prázdne, modul automaticky používa bezplatný štátny register RÚZ / RPO a český ARES.")

    apoliak_finstat_private_key = fields.Char(
        string="FinStat.sk Private Kľúč (Voliteľné)",
        config_parameter='apoliak_finstat_ares.finstat_private_key')

    apoliak_auto_check_vies = fields.Boolean(
        string="Automaticky overovať platcu IČ DPH cez VIES",
        default=True,
        config_parameter='apoliak_finstat_ares.auto_check_vies')
