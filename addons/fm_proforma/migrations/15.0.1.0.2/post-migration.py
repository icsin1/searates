# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for pro_forma_line in env['pro.forma.invoice.line'].sudo().search([('house_shipment_charge_revenue_id', '!=', False)]):
        pro_forma_line.write({
            'shipment_charge_currency_id': pro_forma_line.house_shipment_charge_revenue_id.amount_currency_id.id,
            'currency_exchange_rate': pro_forma_line.house_shipment_charge_revenue_id.amount_conversion_rate
            })
