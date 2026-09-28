# -*- coding: utf-8 -*-
{
    'name': 'Pay by Square (SK) & QR Platba (CZ) — Invoice QR Code',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'Official Slovak Pay by Square (SBA) & Czech QR Platba (SPD) on Odoo PDF Invoices. Offline, zero API fees.',
    'description': """
Pay by Square (SK) & QR Platba (CZ) — Invoice QR Generator
==========================================================
Automatically generates the official Slovak Bank Association **Pay by Square** QR code and Czech **QR Platba (SPD)** directly on Odoo Customer Invoices (PDF & Portal).

Key Features:
-------------
* **100% Offline & Self-Contained**: Uses native LZMA + CRC32 + Base32hex encoding for Slovak Pay by Square. No external paid API or subscription required!
* **Slovak & Czech Bank Apps**: Compatible with Tatra banka, SLSP (George), VÚB, ČSOB, Fio, mBank, UniCredit, Raiffeisen, Air Bank, Komerční banka, Moneta.
* **Automatic Variable Symbol (VS)**: Extracts digits from invoice number (`name` or `payment_reference`) as Variable Symbol (`Variabilný symbol`).
* **PDF Invoice Report Integration**: Automatically prints the QR code with payment details on standard Odoo invoices.
* **Compatible with Odoo 16.0, 17.0, 18.0, 19.0, 20.0** (Community & Enterprise).
    """,
    'author': 'Alex Poliak',
    'website': 'https://apoliak.online',
    'license': 'OPL-1',
    'price': 89.00,
    'currency': 'EUR',
    'depends': [
        'base',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'views/report_invoice.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
