# -*- coding: utf-8 -*-
{
    'name': 'Shipments - Cost as Expense Entry',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Operation',
    'summary': 'Shipments - Cost as Expense Entry',
    'license': 'Other proprietary',
    'description': """
        Shipments - Cost as Expense Entry
    """,
    'depends': ['fm_account_expense_entry', 'freight_management_charges'],
    'data': [
        'security/ir.model.access.csv',
        'views/house_shipment_expense_entry_views.xml',
        'wizard/shipment_expense_entry_wizard_views.xml',
        'wizard/master_shipment_expense_entry_wizard_views.xml',
        'views/account_move_views.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': True
}
