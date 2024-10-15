# -*- coding: utf-8 -*-

{
    'name': 'Freight Quote Multi Carrier',
    'version': '1.0',
    'summary': 'Freight Quote Multi Carrier',
    'description': 'Freight Quote Multi Carrier',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'depends': ['fm_road_quote', 'fm_tariff_quote', 'fm_charge_from_quote'],
    'category': 'Quotation',
    'license': 'Other proprietary',
    'data': [
        'security/ir.model.access.csv',
        'views/shipment_quote_views.xml',
        'views/shipment_quote_line_views.xml',
        'views/tariff_buy_view.xml',
        'views/tariff_sell_view.xml',
        'wizard/wizard_tariff_service_view.xml',
        'wizard/wizard_quote_multi_carrier_charges_view.xml'
    ],
    'installable': True,
    'application': False
}
