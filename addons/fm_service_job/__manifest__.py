# -*- coding: utf-8 -*-
{
    'name': 'Freight Job',
    'version': '1.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Management: Service Job',
    'summary': 'Freight Management Customization specific to Service Job',
    'license': 'Other proprietary',
    'description': """
Freight Service Job Base module

- Service Job Master Data
- Mixin Objects
- Service Job Specific Operational flow
    """,
    'depends': ['freight_base', 'freight_management'],
    'data': [
        'security/freight_service_security.xml',
        'security/ir.model.access.csv',
        'data/fm_job_data.xml',
        'data/res.partner.type.field.csv',
        'data/freight_service_job_data.xml',
        'data/document_type.xml',
        'views/freight_job_type_view.xml',
        'views/freight_measurement_basis_view.xml',
        'views/product_category_view.xml',
        'views/product_template_view.xml',
        'views/freight_service_job_views.xml',
        'views/freight_service_job_event_views.xml',
        'views/freight_service_job_terms_views.xml',
        'views/freight_service_job_document_views.xml',
        'wizard/wizard_service_job_status_view.xml',
        'views/tracking_service_job_portal.xml',
    ],
    'installable': True,
    'application': True,
    'post_init_hook': '_add_service_job_sequence',
}
