# -*- coding: utf-8 -*-
{
    'name': 'Odoo Mail Customization for Account',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Discuss',
    'summary': 'Odoo Mail Customization for Account',
    'license': 'Other proprietary',
    'description': """
Odoo Mail Customization for Account
    """,
    'depends': ['ics_mail', 'account'],
    'data': [
        'views/account_invoice_send_wizard.xml'
    ],
    'installable': True,
    'auto_install': True
}
