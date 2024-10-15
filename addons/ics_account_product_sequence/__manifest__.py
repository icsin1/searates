# -*- coding: utf-8 -*-
{
    'name': 'Account Move Sequence by Product',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Account',
    'summary': '',
    'license': 'Other proprietary',
    'description': """
        Sequence number required as per client requirement,
        sequence number is linked with journals.
    """,
    'depends': ['freight_base', 'ics_account', 'account_move_name_sequence'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_journal.xml'
    ],
    'installable': True,
    'application': False
}
