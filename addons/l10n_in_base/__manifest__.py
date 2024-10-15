# -*- coding: utf-8 -*-
{
    'name': 'Indian - Accounting For Gst Treatment',
    'version': '15.0.0.0.2',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Accounting',
    'summary': '',
    'license': 'Other proprietary',
    'description': """ """,
    'depends': ['l10n_in'],
    'post_init_hook': '_account_l10n_in_post_init',
    'data': [
        'data/account_account_tag_data.xml',
        'views/res_partner_view.xml',
        'views/account_move_view.xml',
        'views/report_invoice.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': True
}
