# -*- coding: utf-8 -*-
{
    'name': 'Freight Sales & CRM',
    'version': '15.0.1.0',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Sales and CRM',
    'summary': 'Sales and CRM',
    'license': 'Other proprietary',
    'description': """ Sales & CRM """,
    'depends': ['freight_base', 'contacts', 'base_address_city', 'freight_management'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/cron.xml',
        'data/sales_team_data.xml',
        'views/res_config_settings_view.xml',
        'views/menu_items.xml',
        'views/sale_target_views.xml',
        'views/organizations_views.xml',
        'views/sales_team_views.xml',
        'views/freight_shipment_views.xml',
        'views/res_partner_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'fm_sale_crm/static/src/js/sales_and_crm_dashboard.js',
        ],
        'web.assets_qweb': [
            'fm_sale_crm/static/src/xml/**/*',
        ],
    },
    'installable': True,
    'application': False
}
