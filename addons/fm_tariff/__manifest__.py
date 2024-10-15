# -*- coding: utf-8 -*-
{
    'name': 'Tariff Management',
    'version': '1.0',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Management',
    'summary': 'Tariff (Buy/Sell) Management',
    'license': 'Other proprietary',
    'description': """ Tariff Management """,
    'depends': ['freight_management_charges'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/menu_items.xml',
        'views/tariff_sell_views.xml',
        'views/tariff_buy_views.xml',
        'wizard/wizard_fetch_charges_to_tariff_views.xml',
        'wizard/wizard_tariff_service_view.xml',
    ],
    'assets': {
        'web.assets_qweb': [
            'fm_tariff/static/src/xml/*.xml',
        ],
        'web.assets_backend': [
            'fm_tariff/static/src/scss/form_view.scss',
        ],
    },
    'installable': True,
    'application': True
}
