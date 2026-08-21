# -*- coding: utf-8 -*-
{
    'name': 'Big Frozen Food - Executive Dashboard',
    'version': '18.0.1.0.0',
    'category': 'Dashboard',
    'summary': 'Executive KPI Dashboard: Sales, Stock Valuation, Low Stock, FEFO Near-Expiry & Supplier Spend',
    'description': """
        Modul Dashboard Eksekutif Big Frozen Food:
        - Dashboard Penjualan: Grafik Omset Harian/Bulanan, Top 5 Produk Terlaris, dan Perbandingan Penjualan Agen vs POS Toko.
        - Dashboard Stok & Kadaluarsa: Card KPI Total Nilai Stok, Jumlah Produk Menipis, dan Jumlah Produk Near-Expiry (FEFO).
        - Dashboard Pembelian: Rekap total belanja ke Supplier bulan ini.
    """,
    'author': 'Big Frozen Food Team',
    'depends': ['base', 'web', 'sale', 'point_of_sale', 'stock', 'purchase', 'bff_stock_control'],
    'data': [
        'security/ir.model.access.csv',
        'views/bff_dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bff_dashboard/static/src/scss/bff_dashboard.scss',
            'bff_dashboard/static/src/xml/bff_dashboard.xml',
            'bff_dashboard/static/src/js/bff_dashboard.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
