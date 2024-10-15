# -*- coding: utf-8 -*-
{
    'name': 'Product Branding',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Product Branding',
    'summary': 'Product Branding',
    'description': """
Labeling/Branding Customization
    """,
    'license': 'Other proprietary',
    'depends': [
        'base', 'web', 'base_import'
    ],
    'data': [
        'data/odoo_branding_data.xml',
        'views/web.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'odoo_branding/static/src/scss/login_page.scss',
        ],
        'web.assets_backend': [
            'odoo_branding/static/src/js/dialog.js',
            'odoo_branding/static/src/js/basic_renderer.js',
            'odoo_branding/static/src/js/user_menu.js',
            'odoo_branding/static/src/js/web_client.js',
            'odoo_branding/static/src/js/error_dialog.js',
        ],
        'web.assets_qweb': [
            'odoo_branding/static/src/xml/*.xml'
        ]
    },
    'application': False,
    'auto_install': True
}
