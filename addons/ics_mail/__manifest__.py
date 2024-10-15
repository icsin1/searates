# -*- coding: utf-8 -*-
{
    'name': 'Odoo Mail Customization',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Discuss',
    'summary': 'Odoo Mail Customization',
    'license': 'Other proprietary',
    'description': """
Odoo Mail Customization
    """,
    'depends': ['mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'wizard/mail_compose_message_views.xml'
    ],
    'installable': True,
    'auto_install': True
}
