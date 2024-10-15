# -*- coding: utf-8 -*-

{
    'name': 'Stimulsoft Document Report',
    'category': 'Utility',
    'version': '15.0.1.2',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'maintainer': 'Intech Creative Services Pvt. Ltd',
    'license': 'Other proprietary',
    'summary': 'Document Report Designer',
    'description': "Document Report Designer",
    'depends': ['odoo_web', 'base_document_reports', 'freight_base_json_data'],
    'data': [
        'security/ir.model.access.csv',
        'views/stimulsoft_report_views.xml',
        'wizard/sample_data_download_wizard_views.xml'
    ],
    'assets': {
        'web.assets_qweb': [
            'base_document_reports_stimulsoft/static/src/xml/stimulsoft_viewer.xml',
        ],
        'web.assets_backend': [
            'base_document_reports_stimulsoft/static/src/libs/stimulsoft/stimulsoft.reports.engine.js',
            'base_document_reports_stimulsoft/static/src/libs/stimulsoft/stimulsoft.reports.export.js',
            'base_document_reports_stimulsoft/static/src/libs/stimulsoft/stimulsoft.viewer.js',
            'base_document_reports_stimulsoft/static/src/js/stimulsoft_viewer.js',
            'base_document_reports_stimulsoft/static/src/scss/stimulsoft_viewer.scss',
            'base_document_reports_stimulsoft/static/src/js/action_menus.js',
            'base_document_reports_stimulsoft/static/src/js/action_manager.js'
        ],
    },
    'application': False
}
