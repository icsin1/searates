# -*- coding: utf-8 -*-
{
    'name': 'Accounting Withholding Tax',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Account',
    'summary': 'Accounting Withholding Tax',
    'license': 'Other proprietary',
    'description': """
        Accounting Withholding Tax
    """,
    'depends': ['payment'],
    'data': [
        'views/account_tax_views.xml',
        'views/account_payment_views.xml',
        'wizard/account_payment_register.xml'
    ],
    'installable': True,
    'application': False
}
