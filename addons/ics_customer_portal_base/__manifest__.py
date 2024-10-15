{
    "name": "Customer Portal Dashboard Base",
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Website/Website',
    'summary': 'Customer Portal Dashboard Base',
    'license': 'Other proprietary',
    'description': """
        Customer Portal Dashboard Base
        """,
    "depends": ["freight_website"],
    "data": [
        "data/website_menu.xml",

        "views/portal.xml"
    ],
    'assets': {
        'web.assets_frontend': [
            'ics_customer_portal_base/static/src/scss/portal.scss',
        ],
    },
    "installable": True,
}
