# -*- coding: utf-8 -*-
{
    'name': 'Currency Rate API Update',
    'version': '15.0.1.0',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'license': 'Other proprietary',
    'category': 'Financial Management/Configuration',
    'description': '''
Currency Rate Base Module:\n
- Update Currency Rates from Configured Rate Provider With API Token (Exchange Rate API)
    ''',
    'depends': ['base', 'mail', 'ics_account'],
    'data': [
        'data/cron.xml',
        'security/ir.model.access.csv',
        'views/res_currency.xml',
        'views/res_currency_rate.xml',
        'views/res_currency_rate_provider.xml'
    ],
    'installable': True,
    'auto_install': True
}
