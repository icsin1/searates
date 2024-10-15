{
    "name": "Customer Portal Account Dashboard",
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Website/Website',
    'summary': 'Customer Portal Account Dashboard',
    'license': 'Other proprietary',
    'description': """
        Customer Portal Account Dashboard
        """,
    "depends": ['ics_customer_portal_base', 'ics_account'],
    "data": [
        'views/portal.xml',
        'views/account_invoice_portal_templates.xml',
        'views/account_credit_note_portal_templates.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'ics_customer_portal_account/static/src/css/account_portal.css',
        ],
    },
    'installable': True,
    'auto_install': True
}
