# -*- coding: utf-8 -*-
{
    'name': 'CargoesFlow Integration',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Integration',
    'summary': 'CargoFlow Container and Air Cargo Tracking',
    'license': 'Other proprietary',
    'description': """
        CargoFlow Container and Air Cargo Tracking
    """,
    'depends': ['freight_management'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/master_shipment_view.xml',
        'views/master_shipment_event_view.xml',
        'views/house_shipment_event_views.xml',
        'views/house_shipment.xml',
        'views/shipment_tracking.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False
}
