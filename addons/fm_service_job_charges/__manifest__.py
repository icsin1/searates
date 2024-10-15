# -*- coding: utf-8 -*-
{
    'name': 'Freight Job Charges',
    'version': '1.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Management: Service Job',
    'summary': 'Freight Management Charges specific to Service Job',
    'license': 'Other proprietary',
    'description': """
Freight Service Job Charge

- Service Job Charges
- Service Charge Invoice/Bill
    """,
    'depends': ['fm_service_job', 'freight_management_charges', ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'views/freight_service_job_views.xml',
        'views/freight_service_job_charge_cost_views.xml',
        'views/freight_service_job_charge_revenue_views.xml',
        'views/freight_service_job_cost_bill_views.xml',
        'views/freight_service_job_revenue_invoice_views.xml',
        'views/res_config_settings.xml',
        'wizard/service_job_charge_bill_wizard_views.xml',
        'wizard/service_job_charge_invoice_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'fm_service_job_charges/static/src/js/*.js',
        ],
        'web.assets_qweb': [
            'fm_service_job_charges/static/src/xml/**/*',
        ],
    },
    'installable': True,
    'application': True,
}
