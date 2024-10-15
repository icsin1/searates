# -*- coding: utf-8 -*-

{
    'name': 'Central Datahub Utility',
    'category': 'Utility',
    'version': '15.0.1.1',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'maintainer': 'Intech Creative Services Pvt. Ltd',
    'license': 'Other proprietary',
    'summary': 'Central Datahub Utility Master',
    'description': "Central Datahub Utility Master",
    'depends': ['odoo_base', 'ics_service_manager'],  # DO NOT ADD ANY DEPENDENCY HERE, AS THIS IS AUTO INSTALL TRUE TO SETUP BASIC THINGS
    'assets': {},
    'data': [
        'security/ir.model.access.csv'
    ],
    'application': False,
    'auto_install': True
}
