# -*- coding: utf-8 -*-
{
    'name': 'Freight Job Tariff',
    'version': '1.0.0',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Management: Service Job',
    'summary': 'Job-Tariff Freight Management Customization',
    'license': 'Other proprietary',
    'description': """
Service Job-Tariff Freight Management
    """,
    'depends': ['fm_tariff', 'fm_tariff_quote', 'fm_service_job_charges', ],
    'data': [
        'views/tariff_buy_view.xml',
        'views/tariff_sell_view.xml',
        'wizard/wizard_tariff_service_view.xml',
    ],
    'assets': {
        'web.assets_qweb': [
            'fm_service_job_tariff/static/src/xml/*.xml',
        ],
    },
    'application': False,
    'auto_install': True,
}
