# -*- coding: utf-8 -*-
{
    'name': 'Web Record View',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Base',
    'summary': 'Odoo Backend Web Customization',
    'license': 'Other proprietary',
    'description': """
Odoo Backend Web Customization
    """,
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            'ics_web_record_view/static/src/js/renderer.js',
        ]
    },
    'installable': True,
    'auto_install': False
}
