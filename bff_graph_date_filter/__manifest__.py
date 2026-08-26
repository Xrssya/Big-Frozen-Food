{
    'name': 'BFF Graph Date Filter',
    'version': '18.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Filter Tanggal Interaktif di Setiap Tampilan Grafik (Graph View)',
    'author': 'Big Frozen Food Team',
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            'bff_graph_date_filter/static/src/scss/graph_date_filter.scss',
            'bff_graph_date_filter/static/src/xml/graph_renderer_patch.xml',
            'bff_graph_date_filter/static/src/js/graph_date_filter.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': True,
    'license': 'LGPL-3',
}
