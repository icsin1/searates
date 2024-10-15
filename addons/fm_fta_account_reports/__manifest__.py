# -*- coding: utf-8 -*-
{
    'name': 'FTA (Federal Tax Authority) Invoice Reports',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Account',
    'summary': 'FTA Invoice Reports',
    'license': 'Other proprietary',
    'description': """
FTA (Federal Tax Authority) Based Invoice Reports for Freight
    """,
    'depends': ['web', 'ics_account', 'freight_management_charges'],
    'data': [
        'security/ir.model.access.csv',
        'views/report_invoice_template.xml',
        'views/report_invoice_fta_template.xml',
        'views/res_partner_bank_views.xml'
    ],
    'assets': {
        'web.report_assets_common': [
            'fm_fta_account_reports/static/src/scss/report_layout_fta.scss'
        ]
    },
    'installable': True,
    'application': False,
    'auto_install': True
}
