# -*- coding: utf-8 -*-
{
    'name': 'ICS Account reconciliation Widget',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Account',
    'summary': 'ICS Accounting',
    'license': 'Other proprietary',
    'description': """
       Account reconciliation Widget Extended
    """,
    'depends': ['account_reconciliation_widget'],
    'assets': {
        'web.assets_backend': [
            'ics_account_reconciliation_widget_extended/static/src/**/*'
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': True
}
