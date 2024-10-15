# -*- coding: utf-8 -*-
{
    'name': 'Odoo Web Bus Customization',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Branding,Base',
    'summary': 'Odoo Web Bus Customization',
    'license': 'Other proprietary',
    'description': """
Odoo Web Bus Customization
    """,
    'depends': ['odoo_web', 'bus'],
    'data': [
        'security/ir.model.access.csv'
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_web_bus/static/src/js/services/*',
        ]
    },
    'installable': True,
    'application': False,
    'auto_install': True
}
