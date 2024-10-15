# -*- coding: utf-8 -*-

{
    'name': 'Document Template',
    'version': '1.0',
    'summary': 'Document Template',
    'description': 'Document Template',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'depends': ['fm_service_job'],
    'data': [
        'security/ir.model.access.csv',
        'views/document_template_views.xml',
        'views/house_shipment_terms_view.xml',
        'views/master_shipment_terms_view.xml',
        'views/service_job_terms_view.xml',
    ],
    'category': 'House, Master and Service Job',
    'license': 'Other proprietary',
    'installable': True,
    'application': False,
}
