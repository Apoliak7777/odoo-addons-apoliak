# -*- coding: utf-8 -*-
{
    'name': 'SK & CZ Bank Auto-Sync & VS Matcher (Fio API, Tatra, SLSP, ČSOB, VÚB)',
    'version': '20.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'Automatic Slovak & Czech bank statement sync (Fio REST API & CAMT.053 XML) with automatic Variable Symbol (VS) invoice matching.',
    'description': """
SK & CZ Bank Auto-Sync & Variable Symbol Matcher
=================================================
Automate bank statement downloads and invoice reconciliation in Odoo Community & Enterprise for Slovak and Czech banks.

Key Features:
-------------
* **Direct Fio Banka REST API Sync**: Automatically pulls new bank transactions for SK and CZ accounts using your Fio API token.
* **ISO 20022 CAMT.053 XML Import**: Native parser for Slovak & Czech bank statements (Tatra banka, Slovenská sporiteľňa, VÚB, ČSOB, Raiffeisen, UniCredit).
* **Smart Variable Symbol (`VS`) Auto-Matching**: Extracts the Slovak/Czech Variable Symbol (`Variabilný symbol`, `/VS...`) and automatically links payments to matching customer invoices and vendor bills.
* **1-Click Sync on Accounting Dashboard**: Sync bank transactions anytime with a single click or scheduled cron.
* **Compatible with Odoo 16.0, 17.0, 18.0, 19.0, 20.0** (Community & Enterprise).
    """,
    'author': 'Alex Poliak',
    'website': 'https://apoliak.online',
    'license': 'OPL-1',
    'price': 190.00,
    'currency': 'EUR',
    'depends': [
        'base',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_journal_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
