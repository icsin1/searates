# -*- coding: utf-8 -*-
{
    'name': 'Accounting Reports',
    'version': '0.0.5',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Account',
    'summary': 'Accounting Reports',
    'license': 'Other proprietary',
    'description': """
Accounting Reports for Management, Audit and Partner Ledgers
    """,
    'depends': ['account', 'account_fiscal_year', 'ics_account', 'ics_report_base_account', ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_finance_report_views.xml',
        'data/mail_template_data.xml',
        'views/account_tax_report_line_views.xml',

        # Report Template
        'reports/report_finance_pdf_template.xml',
        'reports/account_reports.xml',

        # Reports
        'data/profit_and_loss_report_data.xml',
        'data/balance_sheet_report_data.xml',
        'data/account_general_ledger_report_data.xml',
        'data/account_general_trial_balance_data.xml',
        'data/account_partner_ledger_report_data.xml',
        'data/account_aged_partner_account_report_data.xml',
        'reports/balance_confirmation_report_template.xml',
        # Menu
        'views/menu_items.xml',
        'wizard/wiz_balance_confirmation_report_views.xml',
        'wizard/wizard_customer_due_report_view.xml',
    ],
    'assets': {
        'web.assets_qweb': [
            'ics_account_reports/static/src/xml/**/*',
        ],
        'web.assets_backend': [
            'ics_account_reports/static/src/scss/*',
            'ics_account_reports/static/src/js/account_report.js',
            'ics_account_reports/static/src/js/action_manager_account_report.js',
            'ics_account_reports/static/src/js/account_report_section.js',
            'ics_account_reports/static/src/js/account_report_section_line.js',
            'ics_account_reports/static/src/js/finance_report_view.js'
        ],
    },
    'installable': True,
    'application': True,
}
