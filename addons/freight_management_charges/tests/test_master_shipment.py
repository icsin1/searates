# -*- coding: utf-8 -*-

import logging
from .common import FreightShipmentCommon
from odoo.tests import Form
from odoo.tools import mute_logger
from odoo.exceptions import ValidationError
from psycopg2 import IntegrityError

_logger = logging.getLogger(__name__)


class TestMasterShipment(FreightShipmentCommon):

    def test_tc00277_create_master_shipment_directly(self):
        """
        Create a new Master Shipment directly in the system.

        TC No: #TC00277
        """
        _logger.info("\n\n=================== Started TC00277 test case ===================\n")

        # FCL master shipment
        self.assertTrue(self.export_fcl_master_shipment)

        # LCL master shipment
        self.assertTrue(self.export_lcl_master_shipment)

        _logger.info("\n\n=================== Tested TC00277 test case ===================\n")

    def test_attach_house_shipment(self):
        """
        Attach house shipment from Master shipment
        """
        _logger.info("\n\n=================== Started attach house shipment test case ===================\n")

        # Create duplicate House shipment
        self.export_house_shipment.copy()

        # Attach House Shipments
        self.attach_house_shipment(self.export_fcl_master_shipment)

        self.assertEqual(2, len(self.export_fcl_master_shipment.attached_house_shipment_ids.ids))

        _logger.info("\n\n=================== Tested attach house shipment test case ===================\n")

    def test_fetch_from_house_shipment(self):
        """
        'Fetch from House Shipment' functionality in master shipment.
        """
        _logger.info("\n\n=================== Started Fetch from House Shipment test case ===================\n")

        # Attach House Shipment
        house_attach_domain = self.export_fcl_master_shipment.action_attach_house_shipments()
        house_shipment_ids = self.env['freight.house.shipment'].search(house_attach_domain.get('domain'))
        if house_shipment_ids:
            house_shipment_ids[0].with_context(house_attach_domain.get('context')).action_attach_shipment_house()

        self.assertTrue(self.export_fcl_master_shipment.attached_house_shipment_ids)
        self.assertEqual(1, len(self.export_fcl_master_shipment.attached_house_shipment_ids.ids))

        # Create Container
        container_id = self.create_container('CMAU9902401')

        # Create container type
        container_type_id = self.setup_container_type('Twenty foot flatrack', '20FR', 2)

        with Form(self.export_house_shipment) as house_shipment_form:
            with house_shipment_form.container_ids.new() as container_line:
                container_line.container_type_id = container_type_id
                container_line.container_number = container_id

        # Fetch from House Shipment
        self.export_fcl_master_shipment.action_fetch_packages_from_house_shipment()

        self.assertTrue(self.export_fcl_master_shipment.container_ids)
        self.assertEqual(len(self.export_house_shipment.container_ids.ids), len(self.export_fcl_master_shipment.container_ids.ids))

        _logger.info("\n\n=================== Tested Fetch from House Shipment test case ===================\n")

    def add_container(self, container_vals, **kwargs):
        """
        Added a carrier booking type container.

        @param {list} container_vals: list of dictionary
        """
        if kwargs.get('shipment_type') and kwargs.get('shipment_type') == 'lcl':
            export_shipment = self.export_lcl_master_shipment
        else:
            export_shipment = self.export_fcl_master_shipment
        with Form(export_shipment) as master_ship_form:
            for container in container_vals:
                with master_ship_form.carrier_booking_container_ids.new() as carrier_container_line:
                    carrier_container_line.container_type_id = container.get('container_type_id')
                    carrier_container_line.container_mode_id = container.get('container_mode_id')
                    with carrier_container_line.container_number_ids.new() as container_line:
                        container_line.container_number = container.get('container_number')

    def attach_house_shipment(self, master_ship_id):
        """
        Attach House Shipment by clicking on 'Attach Houses' in master shipment.

        @param {recordset} master_ship_id: recordset of freight.master.shipment
        """
        house_attach_domain = master_ship_id.action_attach_house_shipments()
        house_shipment_ids = self.env['freight.house.shipment'].search(house_attach_domain.get('domain'))
        if house_shipment_ids:
            for house_ship in house_shipment_ids:
                house_ship.with_context(house_attach_domain.get('context')).action_attach_shipment_house()

    def test_add_duplicate_carrier_containers_fcl_master_shipment(self):
        """
        Test case for add duplicate carrier booking containers for FCL type master shipment
        Duplicate container should not allow for FCL type.
        """
        _logger.info("\n\n=================== "
                     "Started add duplicate carrier booking container FCL Master Shipment test case "
                     "===================\n")

        # Create container type
        container_type_id = self.setup_container_type('Twenty foot flatrack', '20FR', 2)
        container_40fr_type_id = self.setup_container_type('Forty foot flatrack', '40FR', 2)

        # Add container in Master shipment carrier booking
        container_vals = [
            {
                'container_type_id': container_type_id,
                'container_mode_id': self.env.ref('freight_base.cntr_service_mode_csf_csf'),
                'container_number': 'AOKJ1236200'
            },
            {
                'container_type_id': container_40fr_type_id,
                'container_mode_id': self.env.ref('freight_base.cntr_service_mode_csf_csf'),
                'container_number': 'AOKJ1236200'
            }
        ]

        fm_container_validation_installed = self.env['ir.module.module'].search([('state', '=', 'installed'), ('name', '=', 'fm_container_validation')])
        # Check ValidationError if fm_container_validation_installed is true
        if fm_container_validation_installed:
            with self.assertRaises(ValidationError) as Message:
                self.add_container(container_vals)

            self.assertEqual(str(Message.exception), 'Container number should be unique and not used on other shipments.')
            self.assertFalse(self.export_fcl_master_shipment.carrier_booking_container_ids)

        else:
            self.add_container(container_vals)

            self.assertTrue(self.export_fcl_master_shipment.carrier_booking_container_ids)

        _logger.info("\n\n==================="
                     " Tested add duplicate carrier booking container FCL Master Shipment test case"
                     " ===================\n")

    def test_add_unique_carrier_containers_fcl_master_shipment(self):
        """
        Test case for add unique carrier booking containers for FCL type master shipment
        Unique container should allow for FCL type.
        """
        _logger.info("\n\n==================="
                     "Started add unique carrier booking container FCL Master Shipment test case"
                     "===================\n")

        # Create container type
        container_type_id = self.setup_container_type('Twenty foot flatrack', '20FR', 2)
        container_40fr_type_id = self.setup_container_type('Forty foot flatrack', '40FR', 2)

        # Add container in Master shipment carrier booking
        container_vals = [
            {
                'container_type_id': container_type_id,
                'container_mode_id': self.env.ref('freight_base.cntr_service_mode_csf_csf'),
                'container_number': 'AOKJ1236200'
            },
            {
                'container_type_id': container_40fr_type_id,
                'container_mode_id': self.env.ref('freight_base.cntr_service_mode_csf_csf'),
                'container_number': 'AOKJ1256309'
            }
        ]
        self.add_container(container_vals)
        self.assertTrue(self.export_fcl_master_shipment.carrier_booking_container_ids)
        self.assertEqual(2, len(self.export_fcl_master_shipment.carrier_booking_container_ids))

        _logger.info("\n\n==================="
                     "Tested add unique carrier booking container FCL Master Shipment test case"
                     "===================\n")

    def test_add_duplicate_carrier_containers_lcl_master_shipment(self):
        """
        Test case for add duplicate carrier booking containers for LCL type master shipment
        Duplicate container should not allow for LCL type.
        """
        _logger.info("\n\n=================== "
                     "Started add duplicate carrier booking container LCL Master Shipment test case"
                     "===================\n")

        # Create LCL Type House Shipment
        lcl_house_shipment = self.setup_house_shipment_data(self.export_shipment_type,
                                                            self.lcl_sea_cargo_type,
                                                            self.sea_freight_mode,
                                                            '2023-10-04', self.incoterm_EXW,
                                                            origin_port=self.inmun_origin_port,
                                                            destination_port=self.aejea_destination_port
                                                            )

        # Create container type
        container_type_id = self.setup_container_type('Twenty foot flatrack', '20FR', 2)
        container_40fr_type_id = self.setup_container_type('Forty foot flatrack', '40FR', 2)

        # Add container in Master shipment carrier booking
        container_vals = [
            {
                'container_type_id': container_type_id,
                'container_mode_id': self.env.ref('freight_base.cntr_service_mode_csf_csf'),
                'container_number': 'AOKJ1236200'
            },
            {
                'container_type_id': container_40fr_type_id,
                'container_mode_id': self.env.ref('freight_base.cntr_service_mode_csf_csf'),
                'container_number': 'AOKJ1236200'
            }
        ]

        fm_container_validation_installed = self.env['ir.module.module'].search([('state', '=', 'installed'), ('name', '=', 'fm_container_validation')])
        # Check ValidationError if fm_container_validation_installed is true
        if fm_container_validation_installed:
            with self.assertRaises(ValidationError) as Message:
                self.add_container(container_vals)

            self.assertEqual(str(Message.exception), 'Container number should be unique and not used on other shipments.')
            self.assertFalse(self.export_lcl_master_shipment.carrier_booking_container_ids)
        else:
            self.add_container(container_vals, shipment_type='lcl')
            self.assertTrue(self.export_lcl_master_shipment.carrier_booking_container_ids)

        _logger.info("\n\n=================== "
                     "Tested add duplicate carrier booking container LCL Master Shipment test case "
                     "===================\n")

    def test_add_duplicate_containers_fcl_master_shipment(self):
        """
        Test case for add duplicate containers (Fetch from House Shipment) for FCL type master shipment
        Unique container should not allow for FCL type.
        """
        _logger.info("\n\n==================="
                     "Started add duplicate container FCL Master Shipment test case"
                     "===================\n")

        # Create container type
        container_type = self.setup_container_type('Twenty foot flatrack', '20FR', 2)
        container_40fr_type_id = self.setup_container_type('Forty foot flatrack', '40FR', 2)

        # Add container in house shipment
        with Form(self.export_house_shipment) as house_shipment_form:
            with house_shipment_form.container_ids.new() as container_line:
                container_line.container_type_id = container_type
            with house_shipment_form.container_ids.new() as container_line:
                container_line.container_type_id = container_40fr_type_id

        self.assertTrue(self.export_house_shipment.container_ids)
        self.assertEqual(2, len(self.export_house_shipment.container_ids.ids))

        # Attach House Shipments
        self.attach_house_shipment(self.export_fcl_master_shipment)
        self.assertEqual(1, len(self.export_fcl_master_shipment.attached_house_shipment_ids.ids))

        # Fetch from House Shipment
        self.export_fcl_master_shipment.action_fetch_packages_from_house_shipment()
        self.assertEqual(2, len(self.export_fcl_master_shipment.container_ids.ids))

        # Create Container
        container_number_id = self.create_container('AOKJ1235034')

        # add container_number in existing container
        fm_container_validation_installed = self.env['ir.module.module'].search([('state', '=', 'installed'), ('name', '=', 'fm_container_validation')])
        # Check ValidationError if fm_container_validation_installed is true
        if fm_container_validation_installed:
            with self.assertRaises(ValidationError) as Message:
                for container_id in self.export_fcl_master_shipment.container_ids:
                    container_id.container_number = container_number_id
            self.assertEqual(str(Message.exception), 'Container number should be unique.')
        else:
            for container_id in self.export_fcl_master_shipment.container_ids:
                container_id.container_number = container_number_id
            self.assertTrue(self.export_fcl_master_shipment.container_ids)

        _logger.info("\n\n==================="
                     "Tested add duplicate container FCL Master Shipment test case"
                     "===================\n")

    def test_add_unique_containers_fcl_master_shipment(self):
        """
        Test case for add unique containers (Fetch from House Shipment) for FCL type master shipment
        Unique container should allow for FCL type.
        """
        _logger.info("\n\n==================="
                     "Started add unique container FCL Master Shipment test case"
                     "===================\n")

        # Create container type
        container_type = self.setup_container_type('Twenty foot flatrack', '20FR', 2)
        container_40fr_type_id = self.setup_container_type('Forty foot flatrack', '40FR', 2)

        # Add container in house shipment
        with Form(self.export_house_shipment) as house_shipment_form:
            with house_shipment_form.container_ids.new() as container_line:
                container_line.container_type_id = container_type
            with house_shipment_form.container_ids.new() as container_line:
                container_line.container_type_id = container_40fr_type_id

        self.assertTrue(self.export_house_shipment.container_ids)
        self.assertEqual(2, len(self.export_house_shipment.container_ids.ids))

        # Attach House Shipments
        self.attach_house_shipment(self.export_fcl_master_shipment)
        self.assertEqual(1, len(self.export_fcl_master_shipment.attached_house_shipment_ids.ids))

        # Fetch from House Shipment
        self.export_fcl_master_shipment.action_fetch_packages_from_house_shipment()
        self.assertEqual(2, len(self.export_fcl_master_shipment.container_ids.ids))

        # Create Container
        container_number_id = self.create_container('TLLU0582361')
        container1_number_id = self.create_container('TLAU8779051')

        # add container_number in existing container
        self.export_fcl_master_shipment.container_ids[0].container_number = container_number_id
        self.export_fcl_master_shipment.container_ids[1].container_number = container1_number_id

        self.assertEqual(2, len(self.export_fcl_master_shipment.container_ids.ids))
        self.assertTrue(self.export_fcl_master_shipment.container_ids[0].container_number)
        self.assertEqual('TLLU0582361',
                         self.export_fcl_master_shipment.container_ids[0].container_number.container_number)
        self.assertTrue(self.export_fcl_master_shipment.container_ids[1].container_number)
        self.assertEqual('TLAU8779051',
                         self.export_fcl_master_shipment.container_ids[1].container_number.container_number)

        _logger.info("\n\n==================="
                     "Tested add unique container FCL Master Shipment test case"
                     "===================\n")

    def test_add_duplicate_containers_lcl_master_shipment(self):
        """
        Test case for add duplicate containers (Fetch from House Shipment) for LCL type master shipment
        duplicate container should allow for LCL type.
        """
        _logger.info("\n\n==================="
                     "Started add duplicate container LCL Master Shipment test case"
                     "===================\n")

        # Create LCL Type House Shipment
        lcl_house_shipment = self.setup_house_shipment_data(self.export_shipment_type,
                                                            self.lcl_sea_cargo_type,
                                                            self.sea_freight_mode,
                                                            '2023-10-04', self.incoterm_EXW,
                                                            origin_port=self.inmun_origin_port,
                                                            destination_port=self.aejea_destination_port)

        # Add packages in house shipment
        with Form(lcl_house_shipment) as house_shipment_form:
            with house_shipment_form.package_ids.new() as package_line:
                package_line.package_type_id = self.env.ref('freight_base.pack_uom_amm')
            with house_shipment_form.package_ids.new() as package_line:
                package_line.package_type_id = self.env.ref('freight_base.pack_uom_bal')

        self.assertTrue(lcl_house_shipment.package_ids)
        self.assertEqual(2, len(lcl_house_shipment.package_ids.ids))

        # Attach House Shipments
        self.attach_house_shipment(self.export_lcl_master_shipment)
        self.assertEqual(1, len(self.export_lcl_master_shipment.attached_house_shipment_ids.ids))

        # Fetch from House Shipment
        self.export_lcl_master_shipment.action_fetch_packages_from_house_shipment()
        self.assertEqual(2, len(self.export_lcl_master_shipment.package_ids.ids))

        # Create Container
        container_number_id = self.create_container('AOKJ1235034')

        # add duplicate container_number in existing container
        for container_id in self.export_lcl_master_shipment.package_ids:
            container_id.container_number = container_number_id

        self.assertEqual(2, len(self.export_lcl_master_shipment.package_ids.ids))
        self.assertTrue(self.export_lcl_master_shipment.package_ids[0].container_number)
        self.assertEqual('AOKJ1235034',
                         self.export_lcl_master_shipment.package_ids[0].container_number.container_number)
        self.assertTrue(self.export_lcl_master_shipment.package_ids[1].container_number)
        self.assertEqual('AOKJ1235034',
                         self.export_lcl_master_shipment.package_ids[1].container_number.container_number)

        _logger.info("\n\n==================="
                     "Tested add duplicate container LCL Master Shipment test case"
                     "===================\n")


