# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    move_lines_to_update = env['account.move'].sudo().search([('add_charges_from', 'in', ('house', 'master')), ('booking_reference', '=', False)])

    # # Query Code for reference
    # MoveObj = env['account.move'].sudo()
    # for company in env['res.company'].sudo().search([]):
    #     move_to_update = MoveObj.search([('company_id', '=', company.id), ('add_charges_from', 'in', ('house', 'master')), ('booking_reference', '=', False)])

    #     _logger.info('Updating {}-Move for Company-{}'.format(len(move_to_update), company.name))

    #     move_count = 0
    #     for move in move_to_update:
    #         move_count += 1
    #         _logger.info('Executing migration for {}-{}/{}'.format(move.display_name, move_count, len(move_to_update)))
    #         if move.add_charges_from == 'house' and move.house_shipment_ids:
    #             query = """UPDATE account_move SET booking_reference=(SELECT STRING_AGG(booking_nomination_no, ', ') AS booking_no FROM freight_house_shipment WHERE id in %s) WHERE id = %s"""
    #             cr.execute(query, [tuple(move.house_shipment_ids.ids), move.id])
    #         elif move.add_charges_from == 'master':
    #             query = """UPDATE account_move SET booking_reference=(SELECT STRING_AGG(name, ', ') AS name FROM freight_master_shipment WHERE id in %s) WHERE id = %s"""
    #             cr.execute(query, [tuple(move.master_shipment_ids.ids), move.id])

    for move_line in move_lines_to_update:
        booking_reference = False
        if move_line.add_charges_from == 'house':
            booking_reference = ', '.join(move_line.mapped('house_shipment_ids.booking_nomination_no'))
        elif move_line.add_charges_from == 'master':
            booking_reference = ', '.join(move_line.mapped('master_shipment_ids.name'))
        if booking_reference:
            move_line.write({'booking_reference': booking_reference})
