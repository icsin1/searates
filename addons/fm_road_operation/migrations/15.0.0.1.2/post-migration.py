# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for rec in env['freight.shipment.transportation.details'].search([('transport_mode_id', '=', False)]):
        transport_mode_id = rec.house_shipment_id.transport_mode_id or rec.master_shipment_id.transport_mode_id
        if transport_mode_id:
            rec.write({'transport_mode_id': transport_mode_id.id})
