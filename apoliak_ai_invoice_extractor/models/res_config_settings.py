# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ai_invoice_provider = fields.Selection([
        ('gemini', 'Google Gemini (Odporúčané — najrýchlejšie a najlacnejšie)'),
        ('openai', 'OpenAI (GPT-4o)'),
        ('claude', 'Anthropic Claude 3.5'),
    ], string="AI Poskytovateľ", default='gemini',
       config_parameter='apoliak_ai_invoice_extractor.provider',
       help="Vyberte AI model použitý na vyťažovanie PDF faktúr.")

    ai_invoice_api_key = fields.Char(
        string="AI API Kľúč",
        config_parameter='apoliak_ai_invoice_extractor.api_key',
        help="Zadajte API kľúč od vybraného AI poskytovateľa.")

    ai_invoice_auto_create_partner = fields.Boolean(
        string="Automaticky vytvoriť dodávateľa",
        default=True,
        config_parameter='apoliak_ai_invoice_extractor.auto_create_partner',
        help="Ak dodávateľ podľa IČO / DIČ v Odoo ešte neexistuje, automaticky ho vytvorí.")

    ai_invoice_auto_extract_on_upload = fields.Boolean(
        string="Automatické vyťaženie po nahratí PDF",
        default=True,
        config_parameter='apoliak_ai_invoice_extractor.auto_extract_on_upload',
        help="Akonáhle nahráte PDF prílohu do konceptu dodávateľskej faktúry, spustí sa vyťaženie.")
