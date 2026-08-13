# -*- coding: utf-8 -*-
{
    'name': 'Big Frozen Food - Diskon & Promo',
    'version': '18.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Master Data dan Fitur Khusus Manajemen Diskon & Promo Produk',
    'description': """
        Modul khusus untuk mengelola Master Data Diskon & Promo terpisah dari Daftar Harga.
        - Master Data Promo Diskon (Persentase % / Nominal Rp)
        - Penerapan Otomatis pada Sales Order & POS
        - Batas Periode Promo & Kategori Produk
    """,
    'author': 'Big Frozen Food',
    'depends': ['sale', 'point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/promo_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'big_frozen_food_promo/static/src/js/pos_promo_validation.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
