# -*- coding: utf-8 -*-
{
    'name': 'Branding Website',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Branding/White Labeling for Website',
    'summary': 'Branding/White Labeling for Website',
    'description': """
Labeling/Branding Customization for Website
    """,
    'license': 'Other proprietary',
    'depends': ['odoo_branding', 'website', 'portal'],
    'data': [
        'views/website_layout.xml',
        'views/templates.xml',
        'views/views.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('replace', 'website/static/src/scss/primary_variables.scss', 'odoo_branding_website/static/src/scss/primary_variables.scss',)
        ],
        'web.assets_frontend': [
            'odoo_branding_website/static/src/scss/secondary_variables.scss',
            'odoo_branding_website/static/src/scss/user_custom_bootstrap_overridden.scss',
            'odoo_branding_website/static/src/scss/website_navbar.scss',
            'odoo_branding_website/static/src/scss/website_fonts.scss',
            'odoo_branding_website/static/src/scss/login_page.scss',
        ],
        'web.assets_qweb': [
            'odoo_branding_website/static/src/xml/*.xml',
        ],
    },
    'application': True
}
