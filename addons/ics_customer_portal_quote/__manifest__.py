{
    "name": "Customer Portal Quote Dashboard",
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Website/Website',
    'summary': 'Customer Portal Quote Dashboard',
    'license': 'Other proprietary',
    'description': """
        Customer Portal Quote Dashboard
        """,
    "depends": ["ics_customer_portal_base", 'fm_quote'],
    "data": [
        'views/portal.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {

        'web.assets_frontend': [
            'ics_customer_portal_quote/static/src/js/portal.js',
            'ics_customer_portal_quote/static/src/js/portal_selection_option_modification.js',
        ],

    },

    "installable": True,
    'auto_install': True
}
