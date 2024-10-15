# -*- coding: utf-8 -*-

{
    'name': 'Freight Quote',
    'version': '2.7',
    'summary': 'Freight Quote',
    'description': 'Freight Quote',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'depends': ['base', 'account', 'freight_management_charges', 'fm_sale_crm', 'freight_base', 'crm_prospect_lead', 'fm_dashboard', 'freight_base_portal'],
    'category': 'Quotation',
    'license': 'Other proprietary',
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/docx_data.xml',
        'data/quotation_data.xml',
        'data/opportunity_stage_data.xml',
        'data/cron.xml',
        'data/mail_template_data.xml',
        'data/freight_sequence_data.xml',
        'views/shipment_quote_views.xml',
        'views/shipment_quote_line_views.xml',
        'wizard/wizard_shipment_quote_status_views.xml',
        'views/shipment_quote_template_views.xml',
        'views/freight_shipment_views.xml',
        'views/shipment_quote_portal_templates.xml',
        'views/quotation_change_reason_views.xml',
        'views/freight_quote_document_views.xml',
        'views/shipment_quote_portal_templates.xml',
        'views/res_config_settings_view.xml',
        'views/dashboard.xml',
        'views/freight_quote_route.xml',
        'views/res_config_settings_views.xml',
        'views/tracking_shipment_portal.xml',
        'wizard/wizard_publish_quote_confirmation_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'fm_quote/static/src/js/quote_dashboard.js',
            'fm_quote/static/src/js/many2many_tags_email.js',
        ],
        'web.assets_qweb': [
            'fm_quote/static/src/xml/**/*'
        ],
    },
    'installable': True,
    'application': False,
}
