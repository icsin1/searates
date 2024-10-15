# -*- coding: utf-8 -*-
{
    'name': 'Application Service Manager',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Utility',
    'summary': 'Application Service Manager',
    'license': 'Other proprietary',
    'description': """
Application Service Manager
    """,
    'depends': ['base', 'odoo_base'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'auto_install': True
}
