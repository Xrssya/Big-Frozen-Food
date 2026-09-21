# -*- coding: utf-8 -*-
{
    'name': 'Big Frozen Food - POS Payment Method Cicilan & Penagihan',
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Metode pembayaran cicilan di POS & Pelacakan Penagihan Pelanggan di Modul Invoicing',
    'description': """
        Modul Integrasi Pembayaran Cicilan POS ke Modul Penagihan (Invoicing) Big Frozen Food:
        - Opsi metode pembayaran 'Cicilan' di Point of Sale.
        - Pop-up penentuan Batas Waktu / Tanggal Jatuh Tempo Cicilan langsung di layar kasir POS.
        - Memvalidasi kewajiban mengisi nama pelanggan untuk metode cicilan.
        - Otomatis menerbitkan Faktur Penagihan (account.move) beserta Tanggal Jatuh Tempo saat transaksi POS cicilan selesai.
        - Tampilan & Menu Khusus di Modul Penagihan (Invoicing > Penagihan Cicilan) untuk melacak status cicilan pelanggan (Masih Nyicil, Sudah Jatuh Tempo / Terlambat, Lunas).
        - Rekap sisa cicilan, total dibayar, dan tombol cepat bayar angsuran.
    """,
    'author': 'Big Frozen Food Team',
    'depends': ['point_of_sale', 'account'],
    'data': [
        'views/pos_payment_method_views.xml',
        'views/account_move_cicilan_views.xml',
        'views/res_partner_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'bff_pos_cicilan/static/src/css/pos_cicilan.css',
            'bff_pos_cicilan/static/src/xml/cicilan_due_date_popup.xml',
            'bff_pos_cicilan/static/src/js/pos_cicilan_validation.js',
        ],
    },
    'post_init_hook': '_post_init_hook',
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
