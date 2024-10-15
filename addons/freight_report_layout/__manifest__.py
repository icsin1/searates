# -*- coding: utf-8 -*-
{
    'name': "Freight Report Layout Base",
    'version': '1.0.0',
    'summary': """freight_report_layout""",
    'description': """ freight_report_layout""",
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Utility',
    'license': 'Other proprietary',
    'depends': ['base', 'web'],
    'data': [
        'views/freight_report_layout_view.xml',
        'report/freight_report_layout_template.xml',
        'data/freight_report_layout_data.xml'
    ],
    'assets': {
        'web.report_assets_common': [
            'web/static/fonts/fonts.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': True
}
