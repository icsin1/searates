# -*- coding: utf-8 -*-
{
    'name': 'Road Freight - Sales/CRM',
    'version': '1.0.0',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Management: Road',
    'summary': 'Road Freight - Sales/CRM',
    'license': 'Other proprietary',
    'description': """ Road Freight - Sales/CRM """,
    'depends': ['freight_base', 'fm_road', 'crm_prospect_lead'],
    'data': [
        'views/crm_prospect_lead_views.xml',
        'views/crm_prospect_opportunity_views.xml',
    ],
    'installable': True,
    'application': False
}
