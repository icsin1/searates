# -*- coding: utf-8 -*-
{
    'name': 'India -TDS & TCS Report',
    'version': '0.0.2',
    'category': 'Accounting/Localizations',
    'description': """
        India TDS & TCS Tax Report Module
    """,
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'depends': ['l10n_in', 'ics_account_reports', 'l10n_in_gst_report'],
    'data': [
        'data/account_tax_group_data.xml',
        'data/account_account_template_data.xml',
        'data/account_tds_tax_report_data.xml',
        'data/account_tds_tax_template_data.xml',
        'data/account_tcs_tax_report_data.xml',
        'data/account_tcs_tax_template_data.xml',
        'data/tds_finance_engine_report_data.xml',
        'views/tax_report_views.xml',
    ],
    'post_init_hook': 'l10n_in_tds_tcs_post_init',
    'license': 'Other proprietary',
    'installable': True,
    'application': False
}
