# -*- coding: utf-8 -*-
{
    'name': 'Indian - E-invoicing (EDI)',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Localization',
    'summary': 'Indian - E-invoicing (EDI)',
    'license': 'Other proprietary',
    'description': """
Electronic Data Interchange Integration for Indian Accounting
    """,
    'depends': ['ics_account_edi', 'l10n_in', 'l10n_in_base'],
    'data': [
        'data/einvoice_customer_json_specification_data.xml',
        'data/einvoice_customer_address_json_spec_data.xml',
        'views/edi_pdf_report.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True
}
