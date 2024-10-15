# -*- coding: utf-8 -*-
{
    'name': 'Sea Sailing Schedule integration with Shipments',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Schedule',
    'summary': 'Freight Sailing Schedule integration with Shipments',
    'license': 'Other proprietary',
    'description': """
Freight Sailing Schedule integration with Shipments
    """,
    'depends': ['fm_sailing_schedule', 'freight_management', 'odoo_web_bus', ],
    'data': [
        'security/ir.model.access.csv',
        'views/freight_house_shipment_views.xml',
        'views/freight_master_shipment_views.xml',
        'wizard/sailing_schedule_selector_wizard_views.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': True
}
