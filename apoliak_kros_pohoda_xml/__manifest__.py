# -*- coding: utf-8 -*-
{
    'name': 'KROS Omega & Stormware Pohoda XML Accounting Bridge',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': '1-Click export of Odoo Customer Invoices & Vendor Bills to KROS Omega and Stormware Pohoda XML.',
    'description': """
KROS Omega & Stormware Pohoda XML Accounting Bridge
====================================================
Seamlessly connect Odoo Invoicing & Sales with external Slovak and Czech accounting software **KROS Omega** and **Stormware Pohoda**.

Key Features:
-------------
* **Stormware Pohoda XML v2.0 (`dat:dataPack`)**: Exports issued invoices (`issuedInvoice`), vendor bills (`receivedInvoice`), credit notes, partner addresses (`IČO`, `DIČ`, `IČ DPH`), line items, and VAT summaries.
* **KROS Omega Import Format**: Generates structured KROS Omega exchange files (`R00`/`R01`/`R02`) ready for 1-click import by your external accountant.
* **Date Range & Journal Filter**: Export an entire month or quarter of invoices in 3 seconds.
* **Compatible with Odoo 16.0, 17.0, 18.0, 19.0, 20.0** (Community & Enterprise).
    """,
    'author': 'Alex Poliak',
    'website': 'https://apoliak.online',
    'license': 'OPL-1',
    'price': 219.00,
    'currency': 'EUR',
    'depends': [
        'base',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/export_wizard_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
