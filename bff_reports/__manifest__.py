# -*- coding: utf-8 -*-
{
    'name': 'Big Frozen Food - Modul Laporan Terpusat & Analytics Standar Industri',
    'version': '18.0.1.0.0',
    'category': 'Reporting',
    'summary': 'Pusat Laporan Operasional 100% Bahasa Indonesia: Penjualan, POS, Stok Cold-Chain, FEFO Kadaluarsa, Belanja Pemasok, & Piutang',
    'description': """
        Modul Laporan Terpusat Big Frozen Food (Standar Industri Retail & Wholesale):
        - Laporan Penjualan & POS Kasir Toko
        - Laporan Stok Cold Storage & Monitoring Kadaluarsa FEFO
        - Laporan Analisis Belanja Pemasok & HPP
        - Laporan Keuangan, Umur Piutang Agen & Umur Hutang Supplier
        - Wizard Ekspor Laporan Excel (.xlsx) Standar Industri.
    """,
    'author': 'Big Frozen Food Team',
    'depends': [
        'base',
        'web',
        'sale',
        'point_of_sale',
        'stock',
        'purchase',
        'account',
        'bff_karyawan',
        'bff_stock_control',
        'bff_expiry_control',
        'big_frozen_food_promo',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/bff_pos_order_rules.xml',
        'wizard/bff_report_wizard_views.xml',
        'views/sales_reports_views.xml',
        'views/stock_reports_views.xml',
        'views/purchase_reports_views.xml',
        'views/finance_reports_views.xml',
        'views/bff_waste_ratio_report_views.xml',
        'views/bff_reports_menus.xml',
    ],

    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
