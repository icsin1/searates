# -*- coding: utf-8 -*-
{
    'name': 'INTTRA Sea Sailing Schedule',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Schedule',
    'summary': 'INTTRA Freight Sailing Schedule',
    'license': 'Other proprietary',
    'description': """
INTTRA Freight Sailing Schedule
    """,
    'depends': ['fm_sailing_schedule', 'odoo_web_bus', ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/inttra_sailing_schedule_views.xml',
        'wizard/inttra_schedule_search_wizard_views.xml',
        'wizard/sailing_schedule_selector_wizard_views.xml'
    ],
    'assets': {
        'web.assets_qweb': [
            'fm_inttra_sailing_schedule/static/src/xml/*.xml',
        ],
        'web.assets_backend': [
            'fm_inttra_sailing_schedule/static/src/js/inttra_control_panel.js',
        ],
    },
    'installable': True,
    'application': True,
}
