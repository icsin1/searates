# -*- coding: utf-8 -*-
{
    'name': 'Odoo Open Record on New Tab',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Utility',
    'summary': 'Odoo Open Record on New Tab',
    'license': 'Other proprietary',
    'description': """
Odoo Open Record on New Tab
    """,
    'depends': ['freight_management', 'fm_quote'],
    'data': [
        'views/shipment_quote_views.xml',
        'views/master_shipment_views.xml',
        'views/house_shipment_views.xml',
        'views/house_shipment_charge_cost_views.xml',
        'views/house_shipment_charge_revenue_views.xml',
        'views/master_shipment_charge_cost_views.xml',
        'views/master_shipment_charge_revenue_views.xml',
    ],
    'installable': True,
    'auto_install': True
}
