# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for company in env['res.company'].search([]):
        # Executing for only hlr_generated state as other are already executed in freight_management module migration
        for shipment in env['freight.house.shipment'].search([('company_id', '=', company.id), ('state', 'in', ['hlr_generated'])]):
            shipment._compute_teu_total()
