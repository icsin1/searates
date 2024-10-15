# -*- coding: utf-8 -*-
{
    'name': 'Tanzania - Accounting',
    'version': '0.0.1',
    'icon': '/base/static/img/country_flags/tz.png',
    'category': 'Accounting/Localizations/Account Charts',
    'description': """
Tanzania Accounting Module
    """,
    'summary': '',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'depends': ['account'],
    'data': [
        'data/l10n_tz_chart_data.xml',
        'data/account.account.template.csv',
        'data/account_chart_template_data.xml',
        'data/account_tax_report_data.xml',
        'data/account_withholding_tax_report_data.xml',
        'data/account.tax.group.csv',
        'data/account_tax_template_data.xml',
        'data/account_chart_template_configure_data.xml',
        'data/res_currency_data.xml',
        'views/res_partner_views.xml'
    ],
    'license': 'Other proprietary',
}
