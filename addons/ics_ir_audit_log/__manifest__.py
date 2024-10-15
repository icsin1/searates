# -*- coding: utf-8 -*-
{
    'name': 'Audit Log & Tracking',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Utility',
    'summary': 'Data Model Audit Logs report for CRUD, Login and Action access',
    'license': 'Other proprietary',
    'description': """
Audit Logs for changes done by user in the system for all data models
    """,
    'depends': ['odoo_base_setup'],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'views/ir_model_view.xml',
        'views/audit_log_operation_view.xml',
        'views/audit_log_login_view.xml',
        'views/audit_log_action_view.xml',
        'views/res_config_settings_views.xml'
    ],
    'installable': True,
    'auto_install': False
}
