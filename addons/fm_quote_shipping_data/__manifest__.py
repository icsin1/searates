# -*- coding: utf-8 -*-
{
    'name': 'Shipping Data and Agent Free time',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Schedule',
    'summary': 'Shipping Data and Agent Free time in Quote',
    'license': 'Other proprietary',
    'description': """Shipping Data and Agent Free time in Quote""",
    'depends': ['fm_quote'],
    'data': [
        "security/ir.model.access.csv",
        "views/res_config_settings_view.xml",
        "views/shipment_quote_view.xml",
    ],
    'post_init_hook': '_shipping_data_post_init',
    'installable': True,
    'application': False
}
