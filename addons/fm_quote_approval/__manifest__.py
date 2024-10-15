# -*- coding: utf-8 -*-

{
    'name': 'Freight Quote Approval',
    'version': '0.0.1',
    'summary': 'Freight Quote Approval',
    'description': 'Freight Quote Approval',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'depends': ['fm_quote'],
    'category': 'Quotation',
    'license': 'Other proprietary',
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/mail_template_data.xml',
        'views/shipment_quote_views.xml',
        'views/res_config_settings_view.xml',
        'views/shipment_quote_line_views.xml',
        'wizard/wizard_quote_reject_reason_view.xml',
        'wizard/wizard_shipment_quote_status_views.xml'
    ],
    'installable': True,
    'application': False,
}
