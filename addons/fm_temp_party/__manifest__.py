# -*- coding: utf-8 -*-
{
    'name': 'Temporary Party Creation',
    'version': '1.0',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Management',
    'summary': 'Temporary Party Creation',
    'license': 'Other proprietary',
    'description': """ Temporary Party Creation """,
    'depends': ['fm_road_quote', 'fm_road_operation', 'fm_service_job'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/cm_prospect_opportunity_views.xml',
        'views/quote_views.xml',
        'views/house_shipment_views.xml',
        'views/service_job_views.xml'
    ],
    'assets': {},
    'post_init_hook': '_fm_temp_party_init',
    'installable': True,
    'application': False
}
