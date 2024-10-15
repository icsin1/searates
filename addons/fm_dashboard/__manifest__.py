# -*- coding: utf-8 -*-
{
    'name': 'Freight Dashboard Base',
    'version': '15.0.1.0',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Dashboard',
    'summary': 'Freight Dashboard',
    'license': 'Other proprietary',
    'description': """ Sales & CRM """,
    'depends': ['odoo_web', 'freight_base'],
    'data': [
        'security/ir.model.access.csv',
        'views/menu_items.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True
}
