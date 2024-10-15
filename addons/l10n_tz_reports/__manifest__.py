# -*- coding: utf-8 -*-
{
    'name': 'Tanzania - Accounting Reports',
    'version': '0.0.1',
    'icon': '/base/static/img/country_flags/tz.png',
    'category': 'Accounting/Localizations/Account Charts',
    'description': """
Tanzania Accounting Reports
    """,
    'summary': '',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'depends': ['l10n_tz', 'ics_report_base', 'ics_account_withholding_tax', 'ics_account_reports'],
    'data': [
        'security/ir.model.access.csv',
        'data/l10n_tz_tax_report_data.xml',
        'views/vat_report_views.xml',
        'views/withholding_tax_report.xml'
    ],
    'license': 'Other proprietary',
    'auto_install': True,
    'application': False
}
