# -*- coding: utf-8 -*-
import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        MoveObj = env['account.move'].sudo()
        for company in env['res.company'].sudo().search([]):
            move_to_update = MoveObj.search([('company_id', '=', company.id), ('add_charges_from', 'in', ('house', 'master')), ('booking_reference', '=', False)])

            _logger.info('Updating {}-Move for Company-{}'.format(len(move_to_update), company.name))

            move_count = 0
            for move in move_to_update:
                move_count += 1
                _logger.info('Executing migration for {}-{}/{}'.format(move.display_name, move_count, len(move_to_update)))
                if move.add_charges_from == 'house' and move.house_shipment_ids:
                    query = """UPDATE account_move SET booking_reference=(SELECT STRING_AGG(booking_nomination_no, ', ') AS booking_ref FROM freight_house_shipment WHERE id in %s) WHERE id = %s"""
                    cr.execute(query, [tuple(move.house_shipment_ids.ids), move.id])
                elif move.add_charges_from == 'master' and move.master_shipment_ids:
                    query = """UPDATE account_move SET booking_reference=(SELECT STRING_AGG(name, ', ') AS name FROM freight_master_shipment WHERE id in %s) WHERE id = %s"""
                    cr.execute(query, [tuple(move.master_shipment_ids.ids), move.id])
                # Set Value to related field as query execution will not trigger ORM to auto store value in related field
            cr.execute("""UPDATE account_move_line move_line SET booking_reference=move.booking_reference FROM account_move move WHERE move.id=move_line.move_id AND move_line.company_id=%s""", [
                company.id])

    except Exception as e:
        _logger.warning(e)
        env.cr.commit()
