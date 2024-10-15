# -*- coding: utf-8 -*-
{
    'name': 'Audit Trail',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Utility',
    'summary': 'Audit Trails for changes done by user in the Account Move Lines',
    'license': 'Other proprietary',
    'description': """
Audit Trails for changes done by user in the Account Move Lines
    """,
    'depends': ['ics_ir_audit_log','ics_account_reports'],
    'data': [
        'data/operation_report_data.xml',
        'report/templates.xml',
        'views/audit_log_operation_view.xml',
    ],
    'installable': True,
    'auto_install': False
}
