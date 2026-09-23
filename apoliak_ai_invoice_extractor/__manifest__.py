# -*- coding: utf-8 -*-
{
    'name': 'AI Vendor Bill & Invoice Extractor (Zero-Cost OCR)',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Extract vendor bills, invoices, items, taxes and partners instantly using AI without expensive Odoo IAP credits.',
    'description': """
AI Vendor Bill & Invoice Extractor
===================================
Automatically extract and populate Vendor Bills (Nákupné faktúry) from PDF files using modern AI models (Gemini / OpenAI / Claude).

Key Features:
-------------
* **No expensive Odoo IAP credits**: Pay only standard minimal API costs (fractions of a cent per invoice) or use local AI.
* **Auto Partner Detection**: Detects VAT / IČO, company name and automatically matches or creates the partner.
* **Itemized Lines**: Accurately extracts descriptions, quantities, unit prices, and tax rates.
* **Invoice Reference & Dates**: Automatically fills Invoice Date, Due Date, and Vendor Bill reference number.
* **Multi-currency & Multi-language**: Supports Slovak, Czech, English, German, Polish, Hungarian and global invoice formats.
* Compatible with Odoo 16.0, 17.0, 18.0, 19.0 (Community & Enterprise).
    """,
    'author': 'Alex Poliak',
    'website': 'https://apoliak.online',
    'license': 'OPL-1',
    'price': 149.00,
    'currency': 'EUR',
    'depends': [
        'base',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/account_move_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
