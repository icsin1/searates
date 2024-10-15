# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for move_line in env['account.move.line'].sudo().search(['|', ('house_shipment_charge_revenue_id', '!=', False), ('house_shipment_charge_cost_id', '!=', False)]):
        amount_rate = move_line.house_shipment_charge_revenue_id.amount_rate or move_line.house_shipment_charge_cost_id.amount_rate
        move_line.write({'charge_rate_per_unit': amount_rate})
