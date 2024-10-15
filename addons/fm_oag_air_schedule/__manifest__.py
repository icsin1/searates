# -*- coding: utf-8 -*-
{
    'name': 'OAG Air Schedule API',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Schedule',
    'summary': 'OAG Air Schedule API',
    'license': 'Other proprietary',
    'description': """
        OAG Air Schedule API
    """,
    'depends': ['fm_air_schedule', 'odoo_web_bus', ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/oag_air_schedule_views.xml',
        'wizard/oag_schedule_search_wizard_views.xml',
        'wizard/air_schedule_selector_wizard_views.xml'
    ],
    'assets': {
        'web.assets_qweb': [
            'fm_oag_air_schedule/static/src/xml/*.xml',
        ],
        'web.assets_backend': [
            'fm_oag_air_schedule/static/src/js/oag_control_panel.js',
        ],
    },
    'installable': True,
    'application': True,
}
