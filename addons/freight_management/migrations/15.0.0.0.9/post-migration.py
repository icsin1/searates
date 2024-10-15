# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for company in env['res.company'].search([]):
        # Hard skipping hlr_generated state as that will be covered under fm_road_operation module
        for shipment in env['freight.house.shipment'].search([('company_id', '=', company.id), ('state', 'not in', ['hlr_generated'])]):
            shipment._compute_teu_total()
