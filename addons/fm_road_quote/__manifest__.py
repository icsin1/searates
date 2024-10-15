# -*- coding: utf-8 -*-
{
    'name': 'Road Freight - Quote',
    'version': '1.0.0',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Management: Road',
    'summary': 'Road Freight - Quote',
    'license': 'Other proprietary',
    'description': """ Road Freight - Quote """,
    'depends': ['fm_road_sale_crm', 'fm_road_operation'],
    'data': [
        'security/ir.model.access.csv',
        'views/shipment_quote_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False
}
