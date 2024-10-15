# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for pro_forma_line in env['pro.forma.invoice.line'].sudo().search([('house_shipment_charge_revenue_id', '!=', False)]):
        pro_forma_line.write({
            'charge_rate_per_unit': pro_forma_line.house_shipment_charge_revenue_id.amount_rate,
            })
