# -*- coding: utf-8 -*-
{
    'name': 'Freight Job Cost Sheet',
    'version': '1.0.0',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Management',
    'summary': 'Job Cost Sheet',
    'license': 'Other proprietary',
    'description': """ Job Cost Sheet """,
    'depends': ['freight_management_charges'],
    'data': [
        'security/ir.model.access.csv',
        'report/report_job_cost_sheet.xml',
        'report/job_cost_sheet_report.xml',
        'data/mail_template.xml',
    ],
    'application': False,
    'auto_install': True
}
