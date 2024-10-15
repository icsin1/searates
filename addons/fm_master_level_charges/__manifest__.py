# -*- coding: utf-8 -*-
{
    'name': 'Manage Charges from Master',
    'version': '1.0.3',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Charges',
    'summary': 'Manage Charges from Master',
    'license': 'Other proprietary',
    'description': """ Manage Charges from Master """,
    'depends': ['freight_management_charges'],
    'data': [
        'views/freight_master_charge_cost_views.xml',
        'views/freight_master_charge_revenue_views.xml',
    ],
    'installable': True,
    'application': False
}
