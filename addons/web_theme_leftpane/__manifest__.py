# -*- coding: utf-8 -*-
{
    'name': 'Odoo Web Theme - Left Pane',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Branding,Base',
    'summary': 'Odoo Backend theme with Left Pane',
    'license': 'Other proprietary',
    'description': """
Odoo Backend Theme for Odoo community version with Left Pane
    """,
    'depends': ['web', 'odoo_base', 'web_theme'],
    'data': [
        'security/ir.model.access.csv',
        'security/security_data.xml'
    ],
    'assets': {
        'web._assets_secondary_variables': [
            'web_theme_leftpane/static/src/scss/secondary_variables.scss'
        ],
        # 'web._assets_common_styles': [
        #     ('after', 'web/static/src/legacy/scss/navbar.scss', 'web_theme_leftpane/static/src/scss/navbar.scss')
        # ],
        'web.assets_backend': [
            'web_theme_leftpane/static/src/scss/web_customization.scss',
            'web_theme_leftpane/static/src/scss/backend_ui.scss',
            'web_theme_leftpane/static/src/scss/left_menu.scss',
            'web_theme_leftpane/static/src/scss/webclient_layout.scss',
            'web_theme_leftpane/static/src/js/webclient.js',
            'web_theme_leftpane/static/src/js/navbar.js',
        ],
        'web.assets_qweb': [
            'web_theme_leftpane/static/src/xml/*.xml',
        ]
    },
    'installable': True,
    'application': False,
    'auto_install': True
}
