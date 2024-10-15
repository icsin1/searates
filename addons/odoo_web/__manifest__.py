# -*- coding: utf-8 -*-
{
    'name': 'Odoo Web Base Customization',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Branding,Base',
    'summary': 'Odoo Backend Web Customization',
    'license': 'Other proprietary',
    'description': """
Odoo Backend Web Customization
    """,
    'depends': ['web'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml'
    ],
    'assets': {
        'web.assets_qweb': [
            'odoo_web/static/src/xml/apps.xml',
            'odoo_web/static/src/xml/base.xml',
            'odoo_web/static/src/xml/templates.xml',
            'odoo_web/static/src/xml/web_preview.xml',
        ],
        'web.assets_backend': [
            'web/static/lib/Chart/Chart.js',
            'odoo_web/static/src/js/basic_controller.js',
            'odoo_web/static/src/js/list_controller.js',
            'odoo_web/static/src/js/action_menus.js',
            'odoo_web/static/src/js/basic_fields.js',
            'odoo_web/static/src/js/web_preview.js',
            'odoo_web/static/src/js/pdf_viewer.js',
            'odoo_web/static/src/js/do_action.js',
            'odoo_web/static/src/js/action_report_viewer.js',
            'odoo_web/static/src/js/field_web_preview.js',
            'odoo_web/static/src/js/dashboard.js',
            'odoo_web/static/src/js/components.js',
            'odoo_web/static/src/js/company_service.js',
            'odoo_web/static/src/js/about_us.js',
            'odoo_web/static/src/js/kanban_column.js',
            'odoo_web/static/src/scss/*',
        ]
    },
    'installable': True,
    'auto_install': True
}
