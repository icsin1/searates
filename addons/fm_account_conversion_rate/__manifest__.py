# -*- coding: utf-8 -*-
{
    'name': 'Freight Account Conversation Rate',
    'version': '1.0.2',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Accounting/Accounting',
    'summary': 'Freight Account Conversation Rate',
    'license': 'Other proprietary',
    'description': """ Freight Account Conversation Rate.""",
    'depends': ['freight_management_charges', 'ics_account'],
    'data': [
        'views/account_move_views.xml',
        'views/report_invoice.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': True
}
