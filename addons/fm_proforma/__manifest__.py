# -*- coding: utf-8 -*-
{
    'name': 'Freight Pro-Forma Invoice',
    'version': '15.0.1.0.4',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Management',
    'summary': 'Freight Pro-Forma Invoice',
    'license': 'Other proprietary',
    'description': """ Freight Pro-Forma Invoice """,
    'depends': ['freight_management_charges', 'freight_base_portal'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/docx_data.xml',
        'data/document_type.xml',
        'data/ir_sequence_data.xml',
        'data/mail_template_data.xml',
        'data/freight_sequence_data.xml',
        'views/freight_shipment_house_views.xml',
        'views/freight_house_charge_revenue_views.xml',
        'views/pro_forma_invoice_views.xml',
        'views/pro_forma_invoice_portal_templates.xml',
        'wizard/shipment_charge_pro_forma_invoice_wizard_views.xml'
    ],
    'installable': True,
    'application': True,
}
