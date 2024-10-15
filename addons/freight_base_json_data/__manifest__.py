# -*- coding: utf-8 -*-
{
    'name': 'Freight Product Based JSON Specification Data Generator and API',
    'version': '0.0.2',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Utility',
    'summary': 'Freight Product Based JSON Specification Data Generator and API',
    'license': 'Other proprietary',
    'description': """
Freight Product Based JSON Specification Data Generator and API
    """,
    'depends': ['freight_base'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_json_specification_views.xml',
        'wizard/json_spec_importer_wizard_views.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': True
}
