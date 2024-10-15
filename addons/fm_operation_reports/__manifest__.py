# -*- coding: utf-8 -*-
{
    'name': 'Freight Operation Reports',
    'version': '0.0.3',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Operation',
    'summary': 'Freight Operation Reports',
    'license': 'Other proprietary',
    'description': """
Freight Operation Reports
    """,
    # fixme: remove ics_account_reports one all report migrated to new version
    'depends': ['freight_management_charges', 'ics_account_reports', 'ics_report_base_account', 'ics_report_base'],
    'data': [
        'security/ir.model.access.csv',
        'data/account_vendor_statement_report_data.xml',
        'data/account_customer_statement_report_data.xml',
        'data/partner_outstanding_report_data.xml',
        'views/templates.xml',
        'views/menu_data.xml',
        'views/res_config_settings_views.xml',
        # Reports
        'data/operation_customer_sale_report_data.xml',
        'data/operation_custom_duty_report_data.xml',
        'reports/report_custom_duty_pdf.xml',
        'reports/report_template.xml',
        'wizard/chargewise_estimated_actual_report_view.xml',
        'wizard/shipment_profit_report_view.xml',
        'wizard/shipper_wise_shipment_report_view.xml',
        'wizard/customer_wise_shipment_report_views.xml',
        'report/shipment_profit_report.xml',
        'report/shipment_profit_report_template.xml',
    ],
    'installable': True,
    'application': True,
}
