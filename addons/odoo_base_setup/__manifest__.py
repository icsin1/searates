# -*- coding: utf-8 -*-
{
    'name': 'Odoo Base Setup Customization',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Branding,Base',
    'summary': 'Odoo Base Setup Customization',
    'license': 'Other proprietary',
    'description': """
Odoo Base Setup Customization
    """,
    'depends': ['odoo_base', 'base_setup'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml'
    ],
    'installable': True,
    'auto_install': True
}
