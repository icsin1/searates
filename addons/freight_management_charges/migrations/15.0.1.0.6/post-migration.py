# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    master_shipment = env['freight.master.shipment'].sudo().search([('house_shipment_ids', '!=', False)])
    if master_shipment:
        master_shipment._compute_invoice_from_house_shipment()
        master_shipment._compute_house_shipment_account_moves_count()
    house_shipment = env['freight.house.shipment'].sudo().search([('move_line_ids', '!=', False), ('parent_id', '!=', False)])
    if house_shipment:
        house_shipment._compute_account_moves_count()
    account_move = env['account.move'].sudo().search([])
    if account_move:
        account_move._compute_house_shipment()
