# -*- coding: utf-8 -*-
{
    'name': 'Web Report Engine',
    'version': '0.0.2',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Utility',
    'summary': 'Web Report Engine',
    'license': 'Other proprietary',
    'description': """
Web Report Engine with dynamic columns and actions
    """,
    'depends': ['web', 'base', 'report_xlsx', 'report_csv'],
    'data': [
        'security/ir.model.access.csv',
        'views/web_report_views.xml',
        'views/web_report_line_views.xml',
        'views/web_report_pdf_template.xml',
        'views/web_reports_actions.xml',
    ],
    'assets': {
        'web.assets_qweb': [
            'ics_report_base/static/src/xml/**/*',
        ],
        'web.assets_backend': [
            'ics_report_base/static/src/scss/*',
            'ics_report_base/static/src/js/web_report_action.js',
            'ics_report_base/static/src/js/action_manager_web_report.js',
            'ics_report_base/static/src/js/web_report_section.js',
            'ics_report_base/static/src/js/web_report_section_line.js',
            'ics_report_base/static/src/js/web_report_view.js'
        ],
        'web.report_assets_pdf': [
            'ics_report_base/static/src/scss/web_report.scss',
        ]
    },
    'installable': True,
    'application': False,
    'auto_install': True
}
