# -*- coding: utf-8 -*-
{
    'name': 'Freight Sailing Schedule',
    'version': '0.0.2',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Schedule',
    'summary': 'Freight Sailing Schedule',
    'license': 'Other proprietary',
    'description': """
Freight Sailing Schedule
    """,
    'depends': ['fm_schedule'],
    'data': [
        'security/ir.model.access.csv',
        'views/sailing_schedule_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/sailing_schedule_selector_wizard_views.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': True
}
