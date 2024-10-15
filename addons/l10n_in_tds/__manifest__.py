# -*- coding: utf-8 -*-
{
    'name': 'Accounting TDS',
    'version': '15.0.1.0',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Invoicing',
    'summary': 'Accounting TDS',
    'license': 'Other proprietary',
    'description': """ Accounting TDS.""",
    'depends': ['l10n_in'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/account_tds_rate_views.xml',
        'views/product_view.xml',
        'views/account_move_views.xml',
        'views/res_config_settings_views.xml',
        'reports/report_invoice.xml'
    ],
    'installable': False,
    'application': False,
    'auto_install': False
}
