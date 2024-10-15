# -*- coding: utf-8 -*-
{
    'name': 'Web Customization',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Branding,Base',
    'summary': 'Web Customization',
    'license': 'Other proprietary',
    'description': """
Web Customization
    """,
    'depends': ['web', 'base_setup'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_qweb': [
            'web_customization/static/src/xml/templates.xml',
        ],
        'web.assets_backend': [
            'web_customization/static/src/js/list_renderer.js',
            'web_customization/static/src/js/control_panel.js',
        ]
    },
    'installable': True,
    'auto_install': False
}
