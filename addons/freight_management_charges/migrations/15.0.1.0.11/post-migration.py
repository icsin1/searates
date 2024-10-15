# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    house_cost_charge_obj = env['house.shipment.charge.cost'].sudo()
    for company in env['res.company'].sudo().search([]):
        house_cost_charge_ids = house_cost_charge_obj.search([('company_id', '=', company.id), ('master_shipment_cost_charge_id', '!=', False)])
        for cost_charge in house_cost_charge_ids:
            cost_charge._compute_actual_billed_amount()
