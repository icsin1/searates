# -*- coding: utf-8 -*-
{
    'name': 'Customer Invoice Credit Limit',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Account',
    'summary': '',
    'license': 'Other proprietary',
    'description': """
        Warning / Blocker when customer's due amount reached to credit limit.
        - Company level setting
        - Customer Level override settings and limit set
        - Blocking user to create/post invoice with credit limit
        - Showing warning and allowing to post/create invoice
    """,
    'depends': ['ics_account'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move.xml',
        'views/res_config_settings.xml',
        'views/res_partner.xml'
    ],
    'installable': True,
    'application': False
}
