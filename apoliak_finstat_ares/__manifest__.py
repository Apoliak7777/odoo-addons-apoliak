# -*- coding: utf-8 -*-
{
    'name': 'SK & CZ Company Auto-Fill (FinStat, RPO/RÚZ, ARES & VIES)',
    'version': '20.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Instant Slovak & Czech company lookup by IČO/VAT. Auto-fills Name, Address, DIČ, IČ DPH and checks VIES & tax debtors.',
    'description': """
SK & CZ Company Auto-Fill (FinStat, RÚZ, ARES & VIES)
=====================================================
Automatically fetch and fill company details in Odoo Contacts, CRM, Sales and Invoices just by entering the Company ID (IČO) or VAT number.

Key Features:
-------------
* **Slovakia (SK) Support**: Connects to the official Slovak Register of Financial Statements (RÚZ / RPO) out-of-the-box (free, no API key required) plus optional FinStat.sk API integration.
* **Czech Republic (CZ) Support**: Connects directly to the official Czech Ministry of Finance ARES REST API v3.
* **EU VIES VAT Verification**: Automatically validates EU VAT status (`IČ DPH`) and records verification timestamp.
* **1-Click & On-Change Auto-Fill**: Populates Company Name, Street, City, ZIP, Country, Company Registry (`IČO`), Tax ID (`DIČ`), and VAT (`IČ DPH`).
* **Compatible with Odoo 16.0, 17.0, 18.0, 19.0, 20.0** (Community & Enterprise).
    """,
    'author': 'Alex Poliak',
    'website': 'https://apoliak.online',
    'license': 'OPL-1',
    'price': 149.00,
    'currency': 'EUR',
    'depends': [
        'base',
        'contacts',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
