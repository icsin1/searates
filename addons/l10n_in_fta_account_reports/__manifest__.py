# -*- coding: utf-8 -*-
{
    'name': 'FTA (Federal Tax Authority) Invoice Reports for India',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Account',
    'summary': 'FTA Invoice Reports for India',
    'license': 'Other proprietary',
    'description': """
FTA (Federal Tax Authority) Based Invoice Reports for Freight (India)
    """,
    'depends': ['fm_fta_account_reports', 'l10n_in'],
    'data': [
        'security/ir.model.access.csv',
        'views/report_invoice_template.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': True
}
