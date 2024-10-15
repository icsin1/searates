{
    "name": "Customer Portal Shipment Dashboard",
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Website/Website',
    'summary': 'Customer Portal Shipment Dashboard',
    'license': 'Other proprietary',
    'description': """
        Customer Portal Shipment Dashboard
        """,
    "depends": ["ics_customer_portal_base", 'fm_service_job'],
    "data": [
        'security/ir.model.access.csv',
        'views/portal.xml',
        'views/service_jobs_shipment_portal_templates.xml',
        'views/freight_service_job_document_view.xml',
    ],
    "installable": True,
    'auto_install': True
}
