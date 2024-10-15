# -*- coding: utf-8 -*-
{
    'name': 'Quote-Tariff Management',
    'version': '1.0',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Management',
    'summary': 'Quote-Tariff (Buy/Sell) Management',
    'license': 'Other proprietary',
    'description': """ Quote-Tariff Management """,
    'depends': ['fm_tariff', 'fm_quote'],
    'data': [
        'views/shipment_quote_views.xml',
        'wizard/wizard_tariff_service_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
}
