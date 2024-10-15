# -*- coding: utf-8 -*-
{
    'name': 'Road Freight',
    'version': '1.0.0',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Management: Road',
    'summary': 'Freight Management Customization specific to Road Freight',
    'license': 'Other proprietary',
    'description': """ Road Freight """,
    'depends': ['freight_base'],
    'data': [
        'security/ir.model.access.csv',
        'data/location_type_data.xml',
        'views/freight_truck_number_views.xml',
        'views/freight_location_type_views.xml',
        'views/freight_un_location_views.xml',
    ],
    'installable': True,
    'application': False
}
