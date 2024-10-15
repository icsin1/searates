# -*- coding: utf-8 -*-
{
    'name': 'PDC Management Tool',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Account',
    'summary': 'PDC Management Tool',
    'license': 'Other proprietary',
    'description': """
        PDC Management Tool
    """,
    'depends': ['freight_base', 'ics_account'],
    'data': [
        'security/ir.model.access.csv',
        'data/account_data.xml',
        'data/ir_cron_data.xml',
        'data/mail_template_data.xml',
        'views/pdc_payment_views.xml',
        'views/menu_items.xml',
        'views/res_config_settings_views.xml',
        'views/account_payment_views.xml',
        'wizard/account_payment_register.xml',
    ],
    'post_init_hook': '_ics_account_pdc_init',
    'installable': True,
    'application': False,
}
