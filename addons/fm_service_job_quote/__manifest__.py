# -*- coding: utf-8 -*-
{
    'name': 'Freight Job Quote',
    'version': '1.0.0',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Management: Service Job',
    'summary': 'Job-Quote Freight Management Customization',
    'license': 'Other proprietary',
    'description': """
Service Job-Quote Freight Management

As per Service Job Type
    - Opportunity Changes
    - Quote Template Changes
    - Quote Changes
    - Generate Service Job with data from Quote
    """,
    'depends': ['base', 'fm_service_job', 'fm_service_job_charges', 'fm_quote', ],
    'data': [
        'data/freight_sequence_data.xml',
        'security/ir.model.access.csv',
        'views/crm_prospect_opportunity_view.xml',
        'views/shipment_quote_template_view.xml',
        'views/shipment_quote_view.xml',
        'views/freight_service_job_views.xml',
    ],
    'application': False,
    'post_init_hook': '_add_service_job_sequence',
}
