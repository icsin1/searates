# -*- coding: utf-8 -*-
{
    'name': 'Freight Schedules',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Schedules',
    'summary': 'Freight Schedules',
    'license': 'Other proprietary',
    'description': """
Freight Schedules
    """,
    'depends': ['freight_base'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/menu_items.xml',
        'views/res_config_settings_views.xml'
    ],
    'installable': True,
    'application': False,
}
