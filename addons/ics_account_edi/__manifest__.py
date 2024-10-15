# -*- coding: utf-8 -*-
{
    'name': 'Global e-Invoice Integration',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Accounting/Accounting',
    'summary': 'Global e-Invoice Integration',
    'license': 'Other proprietary',
    'description': """
Global e-Invoice Electronic Data Interchange Integration Base
    """,
    'depends': ['ics_service_manager', 'account_edi', 'freight_base_json_data'],
    'data': [
        'data/cron.xml',
        'data/account_edi_data.xml',
        'data/einvoice_customer_address_json_spec_data.xml',
        'data/einvoice_customer_json_specification_data.xml',
        'data/einvoice_move_line_json_specification_data.xml',
        'data/einvoice_json_specification_data.xml',
        'views/account_move_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': True
}
