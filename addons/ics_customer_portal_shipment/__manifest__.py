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
    "depends": ["ics_customer_portal_base", 'freight_management'],
    "data": [
        'security/ir.model.access.csv',
        'views/portal.xml',
        'views/ff_jobs_shipment_portal_templates.xml',
        'views/freight_house_shipment_document_view.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'ics_customer_portal_shipment/static/src/css/customer_portal_shipment.scss'
        ],
    },
    "installable": True,
    'auto_install': True
}
