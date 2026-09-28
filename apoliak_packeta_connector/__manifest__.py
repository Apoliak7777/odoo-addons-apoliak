# -*- coding: utf-8 -*-
{
    'name': 'Packeta (Zásielkovňa) SK & CZ Shipping & Label Connector',
    'version': '16.0.1.0.0',
    'category': 'Inventory/Delivery',
    'summary': 'Direct Packeta (Zásielkovňa) API integration for Odoo: Pickup points, Z-BOX, COD, and 1-Click PDF/ZPL Label printing.',
    'description': """
Packeta (Zásielkovňa) SK & CZ Shipping & Label Connector
=========================================================
Full integration of **Packeta (Zásielkovňa)** into Odoo Inventory & Sales. Send parcels to Packeta API and print PDF/ZPL shipping labels directly from Odoo Delivery Orders (`stock.picking`).

Key Features:
-------------
* **1-Click Parcel Creation (`createPacket`)**: Sends recipient details, weight, Cash-on-Delivery (Dobierka), and insured value directly to Packeta API.
* **Instant PDF Label Download (`packetLabelPdf`)**: Automatically fetches the official Packeta A6/A4 PDF shipping label and attaches it to the delivery order.
* **Pickup Points & Z-BOX Support**: Supports both Z-Point / Z-BOX pickup locations and Home Delivery (HD) carriers across SK, CZ, HU, PL, RO, DE, AT.
* **Cash on Delivery (Dobierka)**: Automatically populates COD amount from the linked Sale Order or Invoice.
* **Compatible with Odoo 16.0, 17.0, 18.0, 19.0, 20.0** (Community & Enterprise).
    """,
    'author': 'Alex Poliak',
    'website': 'https://apoliak.online',
    'license': 'OPL-1',
    'price': 199.00,
    'currency': 'EUR',
    'depends': [
        'base',
        'stock',
        'sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/stock_picking_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
