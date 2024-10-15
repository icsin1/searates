from datetime import datetime
import logging
from odoo.tests import common

_logger = logging.getLogger(__name__)


class TestPartBL(common.TransactionCase):

    def prepare_house_shipment_vals(self, is_part_bl=False, add_package_and_container=False, is_container_part_bl=False,
                                    used_container=False):
        company = self.env.ref("base.main_company")
        sales_agent_id = self.env['res.users'].search([('login', '=', 'admin')], limit=1)
        shipment_type_id = self.env['shipment.type'].search([('code', '=', 'EXP')], limit=1)
        transport_mode_id = self.env['transport.mode'].search([('mode_type', '=', 'sea')], limit=1)
        cargo_type_id = self.env['cargo.type'].search([('code', '=', 'FCL'),
                                                       ('transport_mode_id', '=', transport_mode_id.id)], limit=1)
        service_mode_id = self.env['freight.service.mode'].search([], limit=1)
        inco_term_id = self.env['account.incoterms'].search([], limit=1)
        client_id = self.env['res.partner'].search([('name', '=', 'Azure Interior')], limit=1)
        shipper_id = self.env['res.partner'].search([('name', '=', 'Brandom Freeman')], limit=1)
        origin_country_id = self.env['res.country'].search([('code', '=', 'AE')], limit=1)
        destination_country_id = self.env['res.country'].search([('code', '=', 'AE')], limit=1)
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
            container_type_id = self.env['freight.container.type'].search([], limit=1)
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

    def test_part_bl_create_house_shipment_normal(self):
        # Case 1: Create house shipment with part BL option true and all the required fields
        shipment_vals = self.prepare_house_shipment_vals(is_part_bl=True, add_package_and_container=False,
                                                         is_container_part_bl=False)
        house_shipment_id = self.create_house_shipment(shipment_vals)
        self.assertTrue(house_shipment_id, msg='PartBL Case 1: Record not created for House shipment with PartBL option'
                                               'true and all the required fields.')
        _logger.info('PartBL Case 1: House shipment with PartBL and all the required fields is created successfully')

    def test_part_bl_create_house_shipment_with_container_package(self):
        # Case 2: Create house shipment with part BL option true and add container which is Part BL
        shipment_vals = self.prepare_house_shipment_vals(is_part_bl=True, add_package_and_container=True,
                                                         is_container_part_bl=True)
        house_shipment_id = self.create_house_shipment(shipment_vals)
        self.assertTrue(house_shipment_id and house_shipment_id.part_bl_ids and house_shipment_id.container_ids,
                        msg='PartBL Case 2: Record not created for House shipment with PartBL option true and add '
                            'container which is Part BL.')
        _logger.info('PartBL Case 2: House shipment with PartBL and add container which is Part BL and Part BL lines '
                     'created successfully')

    def test_part_bl_create_house_shipment_no_part_bl(self):
        # Case 5: Create house shipment with part BL option False and all the required fields
        shipment_vals = self.prepare_house_shipment_vals(is_part_bl=False, add_package_and_container=True,
                                                         is_container_part_bl=False)
        house_shipment_id = self.create_house_shipment(shipment_vals)
        self.assertTrue(house_shipment_id, msg='PartBL Case 5: Record should be created if part BL is false and '
                                               'container is also not part BL')
        _logger.info('PartBL Case 5: Successful')
