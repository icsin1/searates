# -*- coding: utf-8 -*-

from datetime import datetime
import logging
from odoo.tests import common

_logger = logging.getLogger(__name__)


class TestAirWayBill(common.TransactionCase):
    """Test cases for eAWB printing."""

    def prepare_house_shipment_vals(self, is_part_bl=False, add_package_and_container=False, is_container_part_bl=False,
                                    used_container=False):
        """Create house shipment to check air way bill printing with all possible conditions."""
        company = self.env.ref("base.main_company")
        sales_agent_id = self.env['res.users'].search(
            [('login', '=', 'admin')], limit=1)
        shipment_type_id = self.env['shipment.type'].search(
            [('code', '=', 'EXP')], limit=1)
        transport_mode_id = self.env['transport.mode'].search(
            [('mode_type', '=', 'air')], limit=1)
        cargo_type_id = self.env['cargo.type'].search([('code', '=', 'LSE'),
                                                       ('transport_mode_id', '=', transport_mode_id.id)], limit=1)
        service_mode_id = self.env['freight.service.mode'].search([], limit=1)
        inco_term_id = self.env['account.incoterms'].search([], limit=1)
        client_id = self.env['res.partner'].search(
            [('name', '=', 'tomair2')], limit=1)
        shipper_id = self.env['res.partner'].search(
            [('name', '=', 'Brandom Freeman')], limit=1)
        origin_country_id = self.env['res.country'].search(
            [('code', '=', 'AE')], limit=1)
        destination_country_id = self.env['res.country'].search(
            [('code', '=', 'AE')], limit=1)
        origin_un_location_id = self.env['freight.un.location'].search([('country_id', '=', origin_country_id.id)],
                                                                       limit=1)
        destination_un_location_id = self.env['freight.un.location'].search([('country_id', '=',
                                                                              destination_country_id.id)], limit=1)
        vals = {'shipment_date': datetime.today(),
                'company_id': company.id,
                'sales_agent_id': sales_agent_id.id,
                'shipment_type_id': shipment_type_id.id,  # export
                'transport_mode_id': transport_mode_id.id,  # SEA
                'cargo_type_id': cargo_type_id.id,  # FCL
                'service_mode_id': service_mode_id.id,
                'inco_term_id': inco_term_id.id,
                'client_id': client_id.id,
                'shipper_id': shipper_id.id,
                'consignee_id': shipper_id.id,
                'origin_un_location_id': origin_un_location_id.id,
                'destination_un_location_id': destination_un_location_id.id,
                'is_part_bl': is_part_bl,
                'no_of_part_bl': '2'
                }
        if add_package_and_container:
            bl_line_vals = [(0, 0, {'bl_no': 'BL999',
                                    'client_id': client_id.id,
                                    'shipper_id': shipper_id.id,
                                    'consignee_id': shipper_id.id})]
            vals.update({'part_bl_ids': bl_line_vals})
            container_type_id = self.env['freight.container.type'].search(
                [], limit=1)
            domain_container = [('is_part_bl', '=', is_container_part_bl)]
            if used_container:
                domain_container.append(('status', '=', 'used'))
            else:
                domain_container.append(('status', '=', 'unused'))
            is_container_number_part_bl_true = self.env['freight.master.shipment.container.number'].search(
                domain_container, limit=1)
            container_vals = [(0, 0, {'container_type_id': container_type_id.id,
                                      'pack_count': 10,
                                      'container_number': is_container_number_part_bl_true.id})]
            vals.update({'container_ids': container_vals})
        return vals

    def create_house_shipment(self, vals):
        house_shipment_id = self.env['freight.house.shipment'].create(vals)
        return house_shipment_id

    def test_eairway_bill_create_house_shipment_normal(self):
        # Case 1: Create house shipment for E-air way bill.
        shipment_vals = self.prepare_house_shipment_vals(is_part_bl=True, add_package_and_container=False,
                                                         is_container_part_bl=False)
        house_shipment_id = self.create_house_shipment(shipment_vals)
        house_shipment_id.action_print()
        _logger.info(
            '===================== eAWB Print Sucessfully ======================')
