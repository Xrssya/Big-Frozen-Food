# -*- coding: utf-8 -*-
{
    'name': 'Big Frozen Food - Stock Control & Low Stock Alert',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Batas stok minimum, pencegahan stok minus, dan notifikasi stok menipis pada POS & Inventaris',
    'description': """
        Modul khusus manajemen & kontrol stok Big Frozen Food:
        - Batas Stok Minimum (min_stock_alert_qty) per produk.
        - Indikator Visual & Alert Stok Menipis di POS (Hijau, Kuning, Merah).
        - Pemblokiran & Pop-up transaksi POS / Pengiriman yang melebihi stok fisik (Pencegahan Stok Minus).
        - Filter & Menu "Stok Menipis" pada modul Inventaris Odoo.
    """,
    'author': 'Big Frozen Food Team',
    'depends': ['stock', 'point_of_sale', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/inventory_low_stock_views.xml',
        'views/stock_transfer_request_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'bff_stock_control/static/src/css/pos_stock.css',
            'bff_stock_control/static/src/xml/pos_stock_badge.xml',
            'bff_stock_control/static/src/js/pos_stock_validation.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
