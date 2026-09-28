# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    apoliak_packeta_api_password = fields.Char(
        string="Packeta API Password (Heslo API)",
        config_parameter='apoliak_packeta_connector.api_password',
        help="32-znakové API heslo z klientskej sekcie Packeta (client.packeta.com).")

    apoliak_packeta_eshop_sender = fields.Char(
        string="Označenie odosielateľa (E-shop ID)",
        config_parameter='apoliak_packeta_connector.eshop_sender',
        default='moj-eshop.sk',
        help="Názov odosielateľa nastavený v klientskej sekcii Packeta.")

    apoliak_packeta_label_format = fields.Selection([
        ('A6 on A6', 'Termotlačiareň A6 (105x148 mm)'),
        ('A6 on A4', 'Klasická tlačiareň A4 (4 štítky na A4)'),
    ], string="Formát PDF štítkov", default='A6 on A6',
       config_parameter='apoliak_packeta_connector.label_format')
