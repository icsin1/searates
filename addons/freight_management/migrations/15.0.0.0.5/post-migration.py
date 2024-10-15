# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for company in env['res.company'].sudo().search([]):
        sequences = env['freight.sequence'].sudo().search([
            ('company_id', '=', company.id), ('ir_model_id.model', 'in', ['freight.house.shipment', 'freight.master.shipment'])
        ])
        if not sequences:
            company._create_per_company_freight_sequence()
