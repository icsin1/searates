# -*- coding: utf-8 -*-
{
    'name': 'Freight Job Quote',
    'version': '1.0.0',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Management: Service Job',
    'summary': 'Job-Quote Freight Management Customization',
    'license': 'Other proprietary',
    'description': """
Service Job Fetch Charge from Quote
    """,
    'depends': ['fm_service_job_quote', 'fm_charge_from_quote', ],
    'data': [
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_qweb': [
            'fm_service_job_charge_from_quote/static/src/xml/**/*',
        ],
    },
    'application': False,
}
