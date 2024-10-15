# -*- coding: utf-8 -*-

{
    'name': 'Document Reports (Engines)',
    'category': 'Utility',
    'version': '15.0.2.0',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'maintainer': 'Intech Creative Services Pvt. Ltd',
    'license': 'Other proprietary',
    'summary': 'Document Report Designer',
    'description': "Document Report Designer",
    'external_dependencies': {
        'python': ['xlsxwriter'],
    },
    'depends': ['odoo_web', 'odoo_base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/report_output_type.xml',
        'views/docx_template_views.xml',
        'wizard/sample_data_download_wizard_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'base_document_reports/static/src/js/action_manager.js',
            'base_document_reports/static/src/js/action_menus.js'
        ],
    },
    'application': False,
    'auto_install': True
}
