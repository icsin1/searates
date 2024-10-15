# -*- coding: utf-8 -*-
{
    'name': 'UAE VAT Return Reports',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Accounting Reports',
    'summary': 'UAE VAT Return Reports',
    'license': 'Other proprietary',
    'description': """
UAE VAT Return Reports
    """,
    'depends': ['account', 'l10n_ae', 'ics_report_base'],
    'data': [
        'data/vat_report_all.xml',
        'security/ir.model.access.csv',
        'views/vat_return_views.xml',
        'report/vat_return_report.xml',
        'report/vat_return_report_template.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False
}
