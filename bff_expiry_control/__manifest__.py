# -*- coding: utf-8 -*-
{
    'name': 'Big Frozen Food - Expiry Control & Clearance Promo',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Manajemen Kadaluarsa Cold-Chain, FEFO, Near-Expiry Alert, dan Otomatisasi Promo Cuci Gudang',
    'description': """
        Modul khusus pengelolaan masa simpan & kadaluarsa Big Frozen Food:
        - Pengaturan Shelf Life & Ambang Peringatan Kadaluarsa (Near-Expiry Alert Days).
        - Indikator Visual Status Kadaluarsa (Aman, Near-Expiry H-30/H-14, Expired).
        - Otomatisasi Pendaftaran Produk Mendekati Expired ke Promo Cuci Gudang (Clearance Sale).
        - Pengurutan Strategi Stok FEFO (First Expired, First Out).
        - Menu & Filter khusus "Stok Mendekati Expired" pada Odoo Backend & POS.
    """,
    'author': 'Big Frozen Food Team',
    'depends': ['stock', 'product_expiry', 'point_of_sale', 'sale', 'bff_stock_control', 'big_frozen_food_promo'],
    'data': [
        'security/ir.model.access.csv',
        'views/expiry_views.xml',
        'views/expiry_menu.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'bff_expiry_control/static/src/css/pos_expiry.css',
            'bff_expiry_control/static/src/xml/pos_expiry_badge.xml',
            'bff_expiry_control/static/src/js/pos_expiry_patch.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
