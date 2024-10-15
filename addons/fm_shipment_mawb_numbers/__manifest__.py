# -*- coding: utf-8 -*-

{
    'name': 'Freight Shipment MAWB Stock',
    'version': '1.0',
    'summary': 'Freight Shipment MAWB Stock',
    'description': 'Freight Shipment MAWB Stock',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'depends': ['fm_mawb_numbers', 'freight_management'],
    'category': 'Freight Base',
    'license': 'Other proprietary',
    'data': [
        'views/mawb_stock_views.xml',
        'views/freight_master_shipment_views.xml',
        'views/freight_shipment_package_views.xml',
        'views/freight_house_shipment_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'fm_shipment_mawb_numbers/static/src/js/mawb_extend_selection.js',
        ],
    },
    'installable': True,
    'application': False,
}
