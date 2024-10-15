# -*- coding: utf-8 -*-
{
    'name': 'Product Branding for Mail',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Product Branding for Mail',
    'summary': 'Product Branding for Mail',
    'description': """
Labeling/Branding Customization for Mail
    """,
    'license': 'Other proprietary',
    'depends': [
        'odoo_branding',
        'mail',
        'mail_bot'
    ],
    'data': [
        'data/mail_templates.xml',
        'data/mail_data.xml',
    ],
    'application': False,
    'auto_install': True
}
