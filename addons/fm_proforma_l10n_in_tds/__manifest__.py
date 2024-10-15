
# -*- coding: utf-8 -*-
{
    'name': 'Freight Proforma Invoice With TDS',
    'version': '15.0.1.0',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Invoicing',
    'summary': 'Freight Proforma Invoice With TDS',
    'license': 'Other proprietary',
    'description': """ This module enables the generation of proforma invoices with Tax Deducted at Source (TDS) calculation.""",
    'depends': ['fm_l10n_in_tds', 'fm_proforma'],
    'data': [
        'views/proforma_invoice_line_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True
}
