# -*- coding: utf-8 -*-
{
    'name': 'Slovak e-Kasa (ORP / FiskalPRO / Elcom) Fiscal Bridge',
    'version': '20.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'Slovak Financial Administration e-Kasa integration (OKP, UID, DKP & Fiscal Printer bridge for FiskalPRO / Elcom).',
    'description': """
Slovak e-Kasa (ORP / FiskalPRO / Elcom) Fiscal Bridge
=====================================================
Connect Odoo Invoicing & Cash Receipts with Slovak certified **e-Kasa** fiscal printers and ORP (FiskalPRO, Elcom, Varos, Fiskal API).

Key Features:
-------------
* **Mandatory Slovak e-Kasa Fields**: Stores `DKP` (Daňový kód pokladnice), `UID` (Unikátny identifikátor dokladu), and `OKP` (Overovací kód podnikateľa).
* **1-Click Fiscalization**: Sends cash invoice / receipt items to your local e-Kasa fiscal bridge (FiskalPRO / Elcom REST service) and records the official Financial Administration SR UID.
* **e-Kasa QR Verification Code**: Generates the official e-Kasa verification link & QR code for the customer receipt.
* **Compatible with Odoo 16.0, 17.0, 18.0, 19.0, 20.0** (Community & Enterprise).
    """,
    'author': 'Alex Poliak',
    'website': 'https://apoliak.online',
    'license': 'OPL-1',
    'price': 349.00,
    'currency': 'EUR',
    'depends': [
        'base',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
