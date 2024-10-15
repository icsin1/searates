# -*- coding: utf-8 -*-
{
    'name': 'Sea Schedule integration with Quote',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Schedule',
    'summary': 'Freight Schedule integration with Quote',
    'license': 'Other proprietary',
    'description': """
Freight Sea Schedule integration with Quote
    """,
    'depends': ['fm_quote', 'fm_sailing_schedule'],
    'data': [
        'views/shipment_quote_views.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': True
}
