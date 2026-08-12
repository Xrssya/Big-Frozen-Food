{
    'name': 'Big Frozen Food - Sleek POS Receipt',
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Modern, high-resolution thermal receipt layout for Big Frozen Food POS',
    'author': 'Big Frozen Food Team',
    'depends': ['point_of_sale'],
    'data': [],
    'assets': {
        'point_of_sale._assets_pos': [
            'bff_pos_receipt/static/src/css/pos_receipt_custom.css',
            'bff_pos_receipt/static/src/xml/pos_receipt_header.xml',
            'bff_pos_receipt/static/src/xml/pos_order_receipt.xml',
            'bff_pos_receipt/static/src/js/pos_order_line_patch.js',
        ],
        'web.assets_backend': [
            'bff_pos_receipt/static/src/js/price_no_decimals_patch.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
