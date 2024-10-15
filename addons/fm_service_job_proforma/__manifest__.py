# -*- coding: utf-8 -*-
{
    'name': 'Service Job Pro-Forma Invoice',
    'version': '15.0.1.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Management',
    'summary': 'Service Job Pro-Forma Invoice',
    'license': 'Other proprietary',
    'description': """ Service Job Pro-Forma Invoice """,
    'depends': ['fm_proforma', 'fm_service_job_charges'],
    'data': [
        'security/ir.model.access.csv',
        'views/service_job_charge_revenue_views.xml',
        'views/service_job_views.xml',
        'views/proforma_invoice_views.xml',
        'wizard/service_job_charge_pro_forma_invoice_wizard_views.xml'
    ],
    'installable': True,
    'application': True,
}
