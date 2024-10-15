# -*- coding: utf-8 -*-

{
    'name': 'Jaspersoft Document Report',
    'category': 'Utility',
    'version': '15.0.1.0',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'maintainer': 'Intech Creative Services Pvt. Ltd',
    'license': 'Other proprietary',
    'summary': 'Document Report Designer',
    'description': "Document Report Designer",
    'depends': ['base_document_reports', 'freight_base_json_data'],
    'data': [
        'security/ir.model.access.csv',
        'views/jaspersoft_report_views.xml',
        'wizard/sample_data_download_wizard_views.xml'
    ],
    'assets': {
    },
    'application': False
}
