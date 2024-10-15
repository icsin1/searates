# -*- coding: utf-8 -*-
{
    'name': 'Global TDS Tax',
    'version': '15.0.1.0',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Invoicing',
    'summary': 'Accounting Apply Global TDS Taxes on vendor bill',
    'license': 'Other proprietary',
    'description': """ Accounting Apply Global TDS Taxes on vendor bill.""",
    'depends': ['l10n_in', 'l10n_in_tds_tcs', 'ics_account'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'wizard/wizard_account_global_tds_tax_views.xml'
    ],
    'installable': True,
    'application': False
}
