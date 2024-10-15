# -*- coding: utf-8 -*-
{
    'name': 'Service Job - Cost as Expense Entry',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Operation',
    'summary': 'Service Job - Cost as Expense Entry',
    'license': 'Other proprietary',
    'description': """
        Service Job - Cost as Expense Entry
    """,
    'depends': ['fm_account_expense_entry', 'fm_service_job_charges'],
    'data': [
        'security/ir.model.access.csv',
        'views/service_job_expense_entry_views.xml',
        'wizard/freight_job_expense_entry_wizard_views.xml',
        'views/account_move_views.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': True
}
