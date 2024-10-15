# -*- coding: utf-8 -*-
{
    'name': 'Sea Inttra Schedule integration with Quote',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Schedule',
    'summary': 'Freight Sailing Schedule integration with Quote',
    'license': 'Other proprietary',
    'description': """
Freight Sailing Schedule integration with Quote
    """,
    'depends': ['fm_inttra_sailing_schedule', 'fm_quote_schedule'],
    'data': [
        'views/shipment_quote_views.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': True
}
