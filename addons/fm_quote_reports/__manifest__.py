# -*- coding: utf-8 -*-

{
    "name": "Quote Reports",
    'version': '1.0',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    "category": "Quote",
    "description": "Quote Reports",
    'license': 'Other proprietary',
    "description": "Quote Reports",
    "depends": ["fm_quote_approval"],
    "data": [
        'data/mail_template.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/shipment_quote_status_analysis_views.xml',
        'report/sales_agent_report.xml',
        'report/sales_agent_report_template.xml',
        'wizard/wiz_sales_agent_report_view.xml',
        'wizard/opportunity_detail_report_view.xml'
    ],
    'installable': True,
    'application': False,
    'post_init_hook': '_create_quote_history'
}
