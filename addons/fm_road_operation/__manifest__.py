# -*- coding: utf-8 -*-
{
    'name': 'Road Freight Management',
    'version': '0.1.2',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Management: Road',
    'summary': 'Freight Management Customization specific to Road Freight',
    'license': 'Other proprietary',
    'description': """ Road Freight Management """,
    'depends': ['freight_base', 'freight_management_charges', 'fm_road'],
    'data': [
        'security/ir.model.access.csv',
        'views/freight_shipment_house_views.xml',
        'views/freight_house_shipment_package_view.xml',
        'views/freight_truck_number_views.xml',
        'views/freight_shipment_master_views.xml',
        'wizard/wizard_house_shipment_status_view.xml',
        'wizard/wizard_master_shipment_status.xml',
        'views/freight_master_shipment_package_view.xml',
        'views/freight_house_shipment_transportation_details_views.xml',
        'views/freight_master_shipment_transportation_details_views.xml'
    ],
    'installable': True,
    'application': False
}
