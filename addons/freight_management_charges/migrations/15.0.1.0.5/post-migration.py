# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    house_shipment = env['freight.house.shipment'].sudo().search([])
    if house_shipment:
        house_shipment._compute_estimated_margin_percentage()
        house_shipment._compute_received_margin_percentage()
    master_shipment = env['freight.master.shipment'].sudo().search([])
    if master_shipment:
        master_shipment._compute_estimated_margin_percentage()
        master_shipment._compute_received_margin_percentage()
