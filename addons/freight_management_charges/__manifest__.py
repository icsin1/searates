# -*- coding: utf-8 -*-
{
    'name': 'Freight Charges Management (Revenue and Cost)',
    'version': '1.0.11',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Management',
    'summary': 'Freight Charges Management (Revenue and Cost)',
    'license': 'Other proprietary',
    'description': """ Freight Charges Management (Revenue and Cost) """,
    'depends': ['odoo_web', 'freight_management', 'ics_account', 'fm_dashboard', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/freight_house_charge_revenue_views.xml',
        'views/freight_house_cost_bill_views.xml',
        'views/freight_house_charge_cost_views.xml',
        'views/freight_house_shipment_views.xml',
        'views/freight_house_revenue_invoice_views.xml',
        'views/account_move_views.xml',
        'wizard/shipment_charge_invoice_wizard_views.xml',
        'wizard/shipment_charge_bill_wizard_views.xml',
        'wizard/wizard_adjust_charges_with_houses_views.xml',
        'views/freight_master_shipment_views.xml',
        'views/freight_master_charge_revenue_views.xml',
        'views/freight_master_charge_cost_views.xml',
        'views/freight_master_cost_bill_views.xml',
        'views/dashboard.xml',
        'wizard/wizard_upload_charges_views.xml',
        'views/report_invoice.xml',
        'views/product_view.xml',
        'wizard/adjust_invoice_wizard.xml',
        'wizard/adjust_payment_wizard.xml',
        'wizard/master_shipment_charge_bill_wizard_views.xml',
        'wizard/wizard_import_charges_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'freight_management_charges/static/src/js/*.js',
        ],
        'web.assets_qweb': [
            'freight_management_charges/static/src/xml/**/*',
        ],
    },
    'installable': True,
    'application': False
}
