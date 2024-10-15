# -*- coding: utf-8 -*-
{
    'name': 'CRM Prospect',
    'version': '15.0.1.0',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'CRM',
    'summary': 'CRM Prospect',
    'license': 'Other proprietary',
    'description': """ CRM Prospect.""",
    'depends': ['fm_sale_crm', 'phone_validation'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/crm_prospect_views.xml'
    ],
    'installable': True,
    'application': False
}
