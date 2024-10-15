# -*- coding: utf-8 -*-
{
    'name': 'Transportation Details for Quote & opportunity',
    'version': '1.0',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'summary': 'Manage transportation options in the general configuration',
    'sequence': 10,
    'description': """
    This module allows managing transportation options in the general configuration for Opportunity and Quote.
    """,
    'license': 'Other proprietary',
    'category': 'Freight Management',
    'depends': ['fm_road_quote', 'crm_prospect_lead'],
    'data': [
        'security/ir.model.access.csv',
        'views/opportunity_transportation_details_views.xml',
        'views/quote_transportation_detail_views.xml',
        'views/crm_prospect_opportunity_views.xml',
        'views/shipment_quote_views.xml',
        'views/freight_shipment_house_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
