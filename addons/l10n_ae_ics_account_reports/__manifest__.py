# -*- coding: utf-8 -*-
{
    'name': 'UAE Accounting Reports',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Accounting Reports',
    'summary': 'UAE Accounting Reports',
    'license': 'Other proprietary',
    'description': """
UAE Accounting Reports
    """,
    'depends': ['ics_account_reports', 'l10n_ae'],
    'data': [
        'security/ir.model.access.csv',
        'data/account_tax_report_data.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': True
}
