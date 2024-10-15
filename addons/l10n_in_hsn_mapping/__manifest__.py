# -*- coding: utf-8 -*-
{
    'name': 'Indian Accounting - HSN Mapping',
    'version': '0.0.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Accounting',
    'summary': 'Indian Accounting - HSN Mapping',
    'license': 'Other proprietary',
    'description': """
Indian Accounting - HSN Mapping
    """,
    'depends': ['l10n_in','freight_base'],
    'data': ['security/ir.model.access.csv',
             'security/security.xml',
             'views/hsn_master_view.xml',
             'views/charge_master_views.xml'],
    'installable': True,
    'application': False,
    'auto_install': True
}
