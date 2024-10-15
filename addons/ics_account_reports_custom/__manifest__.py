# -*- coding: utf-8 -*-
{
    'name': 'Accounting Reports-Custom',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Account',
    'summary': 'Accounting Reports',
    'license': 'Other proprietary',
    'description': """
Accounting Reports for Invoice Wise Charge Reports
    """,
    'depends': ['ics_account_reports'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/invoice_wise_charge_report_view.xml',
    ],
    'assets': {},
    'installable': True,
    'application': True,
}
