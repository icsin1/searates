# -*- coding: utf-8 -*-
{
    'name': 'Fixed Assets Management',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Account',
    'summary': 'Fixed Assets Management',
    'license': 'Other proprietary',
    'description': """
Fixed Assets Management
    """,
    'depends': ['account_fiscal_year', 'ics_account_deferred_revenue_expense'],
    'data': [
        'security/ir.model.access.csv',
        'views/fixed_assets_views.xml',
        'views/fixed_assets_models.xml',
        'views/account_views.xml',
    ],
    'installable': True,
    'application': False,
}
