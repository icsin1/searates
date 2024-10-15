# -*- coding: utf-8 -*-
{
    'name': 'Freight Quote-Shipment Charges',
    'version': '0.0.3',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight Quote-Shipment Charges',
    'summary': 'Freight Quote-Shipment Charges',
    'license': 'Other proprietary',
    'description': """
    Freight Quote-Shipment Charges
    - Cost & Revenue Services List view Header Button Customization
    """,
    'depends': ['fm_quote', 'freight_management_charges'],
    'data': [
    ],
    'assets': {
        'web.assets_qweb': [
            'fm_charge_from_quote/static/src/xml/*.xml',
        ],
    },
    'application': False,
    'auto_install': True,
}
