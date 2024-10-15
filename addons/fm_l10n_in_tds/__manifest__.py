# -*- coding: utf-8 -*-
{
    'name': 'Freight Management With Accounting TDS',
    'version': '15.0.1.0',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Invoicing',
    'summary': 'Freight Management With Accounting TDS',
    'license': 'Other proprietary',
    'description': """ Freight Management With Accounting TDS.""",
    'depends': ['l10n_in_tds', 'freight_management_charges'],
    'data': [
        'views/freight_house_charge_revenue_views.xml',
        'views/freight_house_charge_cost_views.xml',
        'views/freight_master_charge_revenue_views.xml',
        'views/freight_master_charge_cost_views.xml'
    ],
    'installable': False,
    'application': False,
    'auto_install': False
}
