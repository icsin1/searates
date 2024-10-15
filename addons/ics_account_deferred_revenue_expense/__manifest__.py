# -*- coding: utf-8 -*-
{
    'name': 'Deferred Revenue and Expenses',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Account',
    'summary': 'Deferred Revenue and Expenses',
    'license': 'Other proprietary',
    'description': """
Deferred Revenue and Deferred Expenses Management
    """,
    'depends': ['ics_account', 'account_fiscal_year'],
    'data': [
        'security/ir.model.access.csv',
        'security/asset_security.xml',
        'views/account_asset_view.xml',
        'views/account_views.xml',
        'views/deferred_revenue_models.xml',
        'views/deferred_expense_models.xml',
        'views/account_move_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
}
