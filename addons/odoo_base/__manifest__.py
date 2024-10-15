# -*- coding: utf-8 -*-

{
    'name': 'Odoo Base Customizations',
    'category': 'Utility',
    'version': '15.0.1.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'maintainer': 'Intech Creative Services Pvt. Ltd',
    'license': 'Other proprietary',
    'summary': 'Odoo Base Customization',
    'description': "Odoo Base Customization",
    'depends': ['base', 'web'],  # DO NOT ADD ANY DEPENDENCY HERE, AS THIS IS AUTO INSTALL TRUE TO SETUP BASIC THINGS
    'assets': {},
    'data': [
        'security/ir.model.access.csv',
        'security/odoo_base_security.xml',
        'views/base_document_layout_views.xml',
        'views/res_company_views.xml',
        'views/report_templates.xml',
        'views/ir_ui_menu_views.xml',
        'views/ir_module_views.xml',
        'views/ir_actions_report_view.xml',
    ],
    'application': False,
    'auto_install': True
}
