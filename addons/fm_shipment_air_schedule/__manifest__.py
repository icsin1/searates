# -*- coding: utf-8 -*-
{
    'name': 'Air Sailing Schedule integration with Shipments',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Schedule',
    'summary': 'Freight Air Schedule integration with Shipments',
    'license': 'Other proprietary',
    'description': """
        Freight Air Schedule integration with Shipments
    """,
    'depends': ['fm_air_schedule', 'freight_management'],
    'data': [
        'views/freight_master_shipment_views.xml',
        'views/freight_house_shipment_views.xml',
        'wizard/air_schedule_selector_wizard.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True
}
