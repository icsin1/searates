# -*- coding: utf-8 -*-
{
    'name': 'Freight Air Schedule',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Schedule',
    'summary': 'Freight Air Schedule',
    'license': 'Other proprietary',
    'description': """
Freight Air Schedule
    """,
    'depends': ['fm_schedule'],
    'data': [
        'security/ir.model.access.csv',
        'views/air_schedule_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/air_schedule_selector_wizard_views.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': True
}
