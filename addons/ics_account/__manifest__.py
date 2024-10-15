# -*- coding: utf-8 -*-
{
    'name': 'ICS Accounting',
    'version': '0.0.6',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Account',
    'summary': 'ICS Accounting',
    'license': 'Other proprietary',
    'description': """
        ICS Accounting Customization and Improvements
    """,
    'depends': ['account', 'mail', 'payment', 'odoo_base', 'account_fiscal_year'],
    'data': [
        'data/currency_data.xml',
        'data/mail_template_data.xml',
        'security/ir.model.access.csv',
        'data/report_visible_title.xml',
        'views/account_menu_views.xml',
        'views/payment_views.xml',
        'wizard/adjust_payment_wizard.xml',
        'wizard/reset_to_draft_wizard_view.xml',
        'views/account_group_views.xml',
        'views/res_config_settings_views.xml',
        'views/account_move_views.xml',
        'views/report_invoice_template.xml',
        'views/partner_view.xml',
        'views/account_payment_receipt_views.xml',
        'views/account_account_views.xml',
        'views/res_currency_view.xml',
        'views/invoice_terms_template_views.xml',
        'views/report_payment_receipt_templates.xml',
        'views/ir_sequence_views.xml',
        'wizard/accounting_lock_dates_wizard.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ics_account/static/src/scss/*'
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': True
}
