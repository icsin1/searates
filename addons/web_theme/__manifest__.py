# -*- coding: utf-8 -*-
{
    'name': 'Web Theme Customization',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Branding,Base',
    'summary': 'Web Backend theme',
    'license': 'Other proprietary',
    'description': """
Web Backend Theme
    """,
    'depends': ['odoo_web'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('replace', 'web/static/src/legacy/scss/primary_variables.scss', 'web_theme/static/src/scss/primary_variables.scss')
        ],
        'web._assets_backend_helpers': [
            ('after', 'web/static/src/legacy/scss/bootstrap_overridden.scss', 'web_theme/static/src/scss/bootstrap_overridden.scss')
        ],
        'web._assets_common_styles': [
            ('after', 'web/static/src/legacy/scss/navbar.scss', 'web_theme/static/src/scss/navbar.scss')
        ],
        'web.assets_qweb': [
            'web_theme/static/src/xml/**/*.xml'
        ],
        'web.assets_backend': [
            'web_theme/static/src/scss/web_customization.scss',
            'web_theme/static/src/scss/list_view.scss',
            'web_theme/static/src/scss/kanban_view.scss',
            'web_theme/static/src/scss/control_panel_view.scss',
            'web_theme/static/src/scss/web_dialog.scss'
        ]
    },
    'installable': True,
    'auto_install': True
}
