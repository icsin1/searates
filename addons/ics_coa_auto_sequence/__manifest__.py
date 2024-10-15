# -*- coding: utf-8 -*-
{
    'name': 'COA Auto Sequence Code',
    'version': '15.0.1.0',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Invoicing',
    'summary': 'COA Auto Sequence Code',
    'license': 'Other proprietary',
    'description': """ COA Auto Sequence Code.""",
    'depends': ['account'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/account_type_sequence_views.xml'
    ],
    'installable': True,
    'application': False,
}
