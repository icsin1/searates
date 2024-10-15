# -*- coding: utf-8 -*-
{
    'name': 'Freight Website',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Website',
    'summary': 'Freight Website',
    'license': 'Other proprietary',
    'description': """
        Freight Website
    """,
    'depends': ['website', 'portal', 'freight_base', 'freight_management'],
    'data': [
        'views/terms_template.xml',
        'data/website_data.xml',
        'views/portal_templates.xml',
        'views/website_contactus_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'freight_website/static/src/scss/tracking_progress_bar.scss',
            'freight_website/static/src/css/feather.css'
        ],
    },
    'installable': True,
    'application': True,
}
