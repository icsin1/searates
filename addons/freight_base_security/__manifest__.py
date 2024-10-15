# -*- coding: utf-8 -*-
{
    'name': 'User Role Management',
    'version': '0.0.3',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'User Role Management',
    'summary': 'User Role Management',
    'description': """
        User Role Management
    """,
    'license': 'Other proprietary',
    'depends': ['odoo_web', 'freight_base'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/res_user_role_views.xml',
        'views/res_users_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'freight_base_security/static/src/**/*.js',
        ],
        'web.assets_qweb': [
            'freight_base_security/static/src/xml/*.xml',
        ],
    },
    'application': False,
    'auto_install': True
}
