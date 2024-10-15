# -*- coding: utf-8 -*-

import logging
from .common import TariffCommon
from odoo.tests import Form
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class TestTariff(TariffCommon):

    def create_sell_tariff(self, shipment_type_id, transport_mode_id, currency_id, cargo_type_id, **kwargs):
        """
        Create Sell Tariff.

        @param {recordset} shipment_type_id: record of 'shipment.type'
        @param {recordset} transport_mode_id: record of 'transport.mode'
        @param {recordset} currency_id: record of 'res.currency'
        @param {recordset} cargo_type_id: record of 'cargo.type'
        @returns {recordset}: record of 'tariff.sell'
        """
        sell_tariff_form = Form(self.env['tariff.sell'])
        sell_tariff_form.shipment_type_id = shipment_type_id
        sell_tariff_form.transport_mode_id = transport_mode_id
        sell_tariff_form.currency_id = currency_id
        sell_tariff_form.cargo_type_id = cargo_type_id
        if kwargs.get('customer_id'):
            sell_tariff_form.customer_id = kwargs.get('customer_id')
        sell_tariff_id = sell_tariff_form.save()

        if kwargs.get('charges'):
            # Add charges
            with Form(sell_tariff_id) as sell_tariff_form:
                for charge in kwargs.get('charges'):
                    with sell_tariff_form.line_ids.new() as sell_tariff_line:
                        sell_tariff_line.unit_price = charge['unit_price']
                        sell_tariff_line.currency_id = charge['currency_id']
                        sell_tariff_line.charge_type_id = charge['charge_type_id']
                        sell_tariff_line.measurement_basis_id = charge['measurement_basis_id']

        return sell_tariff_id

    def create_buy_tariff(self, shipment_type_id, transport_mode_id, currency_id, cargo_type_id, **kwargs):
        """
        Create Buy Tariff.

        @param {recordset} shipment_type_id: record of 'shipment.type'
        @param {recordset} transport_mode_id: record of 'transport.mode'
        @param {recordset} currency_id: record of 'res.currency'
        @param {recordset} cargo_type_id: record of 'cargo.type'
        @returns {recordset}: record of 'tariff.buy'
        """
        buy_tariff_form = Form(self.env['tariff.buy'])
        buy_tariff_form.shipment_type_id = shipment_type_id
        buy_tariff_form.transport_mode_id = transport_mode_id
        buy_tariff_form.currency_id = currency_id
        buy_tariff_form.cargo_type_id = cargo_type_id
        if kwargs.get('vendor_id'):
            buy_tariff_form.vendor_id = kwargs.get('vendor_id')
        buy_tariff_id = buy_tariff_form.save()

        if kwargs.get('charges'):
            # Add charges
            with Form(buy_tariff_id) as buy_tariff_form:
                for charge in kwargs.get('charges'):
                    with buy_tariff_form.line_ids.new() as buy_tariff_line:
                        buy_tariff_line.unit_price = charge['unit_price']
                        buy_tariff_line.currency_id = charge['currency_id']
                        buy_tariff_line.charge_type_id = charge['charge_type_id']
                        buy_tariff_line.measurement_basis_id = charge['measurement_basis_id']
        return buy_tariff_id

    def test_tc00161_fetch_sell_tariff_house_revenue_charges(self):
        """
        Test Case for 'Fetch Sell Tariff' functionality for revenue charges in the house shipment.

        TC No: #TC00161
        """
        _logger.info("\n\n=================== Started TC00161 test case ===================\n")
        # Get customer
        customer_id = self.setup_partner_data('Dora', company_type='person', category_ids=[self.customer_party_type])

        # set multiple charges in sell tariff
        sell_charges_dict = [
            {'charge_type_id': self.delivery_product.product_variant_id,
             'measurement_basis_id': self.shipment_basis_measure,
             'unit_price': 500,
             'currency_id': self.env.ref('base.INR'),
             'date_from': '2023-08-30',
             'date_to': '2023/12/31'}
        ]

        # Create SEA transport mode type Sell Tariff
        sea_sell_tariff_id = self.create_sell_tariff(self.export_shipment_type, self.sea_freight_mode,
                                                     self.env.ref('base.INR'), self.fcl_sea_cargo_type,
                                                     customer_id=customer_id,
                                                     charges=sell_charges_dict)

        # Change customer in house shipment
        self.export_house_shipment.client_id = customer_id

        # create tariff service wizard
        wiz_tariff_service = self.env['tariff.service.wizard'].create({
            'house_shipment_id': self.export_house_shipment.id,
            'shipment_type_id': self.export_shipment_type.id,
            'transport_mode_id': self.sea_freight_mode.id,
            'cargo_type_id': self.fcl_sea_cargo_type.id,
            'origin_id': self.export_house_shipment.origin_un_location_id.id,
            'destination_id': self.export_house_shipment.destination_un_location_id.id,
            'company_id': self.export_house_shipment.company_id.id,
            'customer_id': customer_id.id,
            'sell_charge_master': True,
            'tariff_type': 'sell_tariff',
            'tariff_for': 'shipment',
            'ignore_location': True,
        })

        # Call onchange method for fetch service lines
        wiz_tariff_service._onchange_criteria()
        self.assertEqual(1, len(wiz_tariff_service.tariff_service_line_ids))

        _logger.info("\n\n=================== Tested TC00161 test case ===================\n")

    def test_tc00234_fetch_buy_tariff_house_cost_charges(self):
        """
        Test Case for 'Fetch Buy Tariff' functionality for cost charges in the house shipment.

        TC No: #TC00234
        """
        _logger.info("\n\n=================== Started TC00234 test case ===================\n")
        # Get Vendor
        vendor_id = self.setup_partner_data('Nick', company_type='person', category_ids=[self.vendor_party_type])

        # set multiple charges in sell tariff
        charges_dict = [
            {'charge_type_id': self.delivery_product.product_variant_id,
             'measurement_basis_id': self.shipment_basis_measure,
             'unit_price': 500,
             'currency_id': self.env.ref('base.INR'),
             'date_from': '2023/09/18',
             'date_to': '2024/09/18'},
            {'charge_type_id': self.main_carriage_product.product_variant_id,
             'measurement_basis_id': self.shipment_basis_measure,
             'unit_price': 200,
             'currency_id': self.env.ref('base.INR'),
             'date_from': '2023/09/18',
             'date_to': '2024/09/18'}
        ]

        # Create SEA transport mode type Buy Tariff
        sea_buy_tariff_id = self.create_buy_tariff(self.export_shipment_type, self.sea_freight_mode,
                                                   self.env.ref('base.INR'), self.fcl_sea_cargo_type,
                                                   vendor_id=vendor_id,
                                                   charges=charges_dict)

        # Change customer in house shipment
        self.export_house_shipment.client_id = vendor_id

        # create tariff service wizard
        wiz_tariff_service = self.env['tariff.service.wizard'].create({
            'house_shipment_id': self.export_house_shipment.id,
            'shipment_type_id': self.export_shipment_type.id,
            'transport_mode_id': self.sea_freight_mode.id,
            'cargo_type_id': self.fcl_sea_cargo_type.id,
            'origin_id': self.export_house_shipment.origin_un_location_id.id,
            'destination_id': self.export_house_shipment.destination_un_location_id.id,
            'company_id': self.export_house_shipment.company_id.id,
            'customer_id': vendor_id.id,
            'sell_charge_master': True,
            'tariff_type': 'buy_tariff',
            'tariff_for': 'shipment',
            'ignore_location': True,
        })

        # Call onchange method for fetch service lines
        wiz_tariff_service._onchange_criteria()
        self.assertEqual(2, len(wiz_tariff_service.tariff_service_line_ids))

        _logger.info("\n\n=================== Tested TC00234 test case ===================\n")

    def test_tc00338_create_sell_tariff_for_customer_without_charges(self):
        """
        Test Case for create a new sell tariff for a customer without adding charges.

        TC No: #TC00338
        """
        _logger.info("\n\n=================== Started TC00338 test case ===================\n")

        # Get customer
        customer_id = self.setup_partner_data('Dora', company_type='person', category_ids=[self.customer_party_type])

        # Create SEA transport mode type Sell Tariff
        sea_sell_tariff_id = self.create_sell_tariff(self.export_shipment_type, self.sea_freight_mode,
                                                     self.env.ref('base.INR'), self.fcl_sea_cargo_type,
                                                     customer_id=customer_id)

        self.assertTrue(sea_sell_tariff_id)
        self.assertTrue(sea_sell_tariff_id.customer_id)
        self.assertFalse(sea_sell_tariff_id.line_ids)

        # Create ROAD transport mode type Sell Tariff
        land_sell_tariff_id = self.create_sell_tariff(self.export_shipment_type, self.land_freight_mode,
                                                      self.env.ref('base.INR'), self.ftl_land_cargo_type,
                                                      customer_id=customer_id)
        self.assertTrue(land_sell_tariff_id)
        self.assertTrue(land_sell_tariff_id.customer_id)
        self.assertFalse(sea_sell_tariff_id.line_ids)

        _logger.info("\n\n=================== Tested TC00338 test case ===================\n")

    def test_tc00342_create_sell_tariff_for_customer_with_charges(self):
        """
        Test Case for create a new sell tariff for a customer with adding charges.

        TC No: #TC00342
        """
        _logger.info("\n\n=================== Started TC00342 test case ===================\n")

        # Get customer
        customer_id = self.setup_partner_data('Dora', company_type='person', category_ids=[self.customer_party_type])

        # set multiple charges in sell tariff
        sell_charges_dict = [
            {'charge_type_id': self.delivery_product.product_variant_id,
             'measurement_basis_id': self.shipment_basis_measure,
             'unit_price': 500,
             'currency_id': self.env.ref('base.INR'),
             'date_from': '2023-08-30',
             'date_to': '2023/12/31'}
        ]

        # Create SEA transport mode type Sell Tariff
        sea_sell_tariff_id = self.create_sell_tariff(self.export_shipment_type, self.sea_freight_mode,
                                                     self.env.ref('base.INR'), self.fcl_sea_cargo_type,
                                                     customer_id=customer_id,
                                                     charges=sell_charges_dict)

        self.assertTrue(sea_sell_tariff_id)
        self.assertTrue(sea_sell_tariff_id.customer_id)
        self.assertTrue(sea_sell_tariff_id.line_ids)
        self.assertEqual(1, len(sea_sell_tariff_id.line_ids))
        self.assertEqual('Dora-EXPSEAFCL', sea_sell_tariff_id.tariff_name)

        buy_charges_dict = [
            {'charge_type_id': self.delivery_product.product_variant_id,
             'measurement_basis_id': self.shipment_basis_measure,
             'unit_price': 500,
             'currency_id': self.env.ref('base.INR'),
             'date_from': '2023/09/18',
             'date_to': '2024/09/18'},
            {'charge_type_id': self.main_carriage_product.product_variant_id,
             'measurement_basis_id': self.shipment_basis_measure,
             'unit_price': 200,
             'currency_id': self.env.ref('base.INR'),
             'date_from': '2023/09/18',
             'date_to': '2024/09/18'}
        ]

        # Create ROAD transport mode type Sell Tariff
        land_sell_tariff_id = self.create_sell_tariff(self.export_shipment_type, self.land_freight_mode,
                                                      self.env.ref('base.INR'), self.ftl_land_cargo_type,
                                                      customer_id=customer_id, charges=buy_charges_dict)
        self.assertTrue(land_sell_tariff_id)
        self.assertTrue(land_sell_tariff_id.customer_id)
        self.assertTrue(land_sell_tariff_id.line_ids)
        self.assertEqual(2, len(land_sell_tariff_id.line_ids))
        self.assertEqual('Dora-EXPROEFTL', land_sell_tariff_id.tariff_name)

        _logger.info("\n\n=================== Tested TC00342 test case ===================\n")

    def test_tc00348_duplicate_sell_tariff(self):
        """
        Test Case for duplicate sell tariff.

        TC No: #TC00348
        """
        _logger.info("\n\n=================== Started TC00348 test case ===================\n")
        # Get customer
        customer_id = self.setup_partner_data('Dora', company_type='person', category_ids=[self.customer_party_type])

        # set multiple charges in sell tariff
        charges_dict = [
            {'charge_type_id': self.delivery_product.product_variant_id,
             'measurement_basis_id': self.shipment_basis_measure,
             'unit_price': 500,
             'currency_id': self.env.ref('base.INR'),
             'date_from': '2023/09/18',
             'date_to': '2024/09/18'}
        ]

        # Create SEA transport mode type Sell Tariff
        sea_sell_tariff_id = self.create_sell_tariff(self.export_shipment_type, self.sea_freight_mode,
                                                     self.env.ref('base.INR'), self.fcl_sea_cargo_type,
                                                     customer_id=customer_id,
                                                     charges=charges_dict)
        copy_sea_tariff_id = sea_sell_tariff_id.copy()
        self.assertTrue(copy_sea_tariff_id)
        self.assertFalse(copy_sea_tariff_id.customer_id)
        self.assertTrue(copy_sea_tariff_id.line_ids)
        self.assertEqual(sea_sell_tariff_id.shipment_type_id, copy_sea_tariff_id.shipment_type_id)
        self.assertEqual(sea_sell_tariff_id.cargo_type_id, copy_sea_tariff_id.cargo_type_id)
        self.assertEqual(sea_sell_tariff_id.transport_mode_id, copy_sea_tariff_id.transport_mode_id)
        self.assertEqual(sea_sell_tariff_id.company_id, copy_sea_tariff_id.company_id)
        self.assertEqual(sea_sell_tariff_id.currency_id, copy_sea_tariff_id.currency_id)
        self.assertEqual(len(sea_sell_tariff_id.line_ids), len(copy_sea_tariff_id.line_ids))
        self.assertEqual('EXPSEAFCL', copy_sea_tariff_id.tariff_name)

        _logger.info("\n\n=================== Tested TC00348 test case ===================\n")

    def test_tc01511_duplicate_buy_tariff(self):
        """
        Test Case for duplicate Buy tariff.

        TC No: #TC01511
        """
        _logger.info("\n\n=================== Started TC01511 test case ===================\n")
        # Get Vendor
        vendor_id = self.setup_partner_data('Nick', company_type='person', category_ids=[self.vendor_party_type])

        # set multiple charges in sell tariff
        charges_dict = [
            {'charge_type_id': self.delivery_product.product_variant_id,
             'measurement_basis_id': self.shipment_basis_measure,
             'unit_price': 500,
             'currency_id': self.env.ref('base.INR'),
             'date_from': '2023/09/18',
             'date_to': '2024/09/18'}
        ]

        # Create SEA transport mode type Buy Tariff
        sea_buy_tariff_id = self.create_buy_tariff(self.export_shipment_type, self.sea_freight_mode,
                                                   self.env.ref('base.INR'), self.fcl_sea_cargo_type,
                                                   vendor_id=vendor_id,
                                                   charges=charges_dict)

        with self.assertRaises(ValidationError) as Message:
            copy_sea_tariff_id = sea_buy_tariff_id.copy()

        self.assertEqual(str(Message.exception), 'Nick-EXPSEAFCL already defined with same Buy tariff criteria!')

        _logger.info("\n\n=================== Tested TC01511 test case ===================\n")

    def test_tc00407_create_buy_tariff_for_customer_with_charges(self):
        """
        Test Case for create a new buy tariff for a customer with adding charges.

        TC No: #TC00407
        """
        _logger.info("\n\n=================== Started TC00407 test case ===================\n")

        # Get Vendor
        vendor_id = self.setup_partner_data('Nick', company_type='person', category_ids=[self.vendor_party_type])

        # set multiple charges in sell tariff
        charges_dict = [
            {'charge_type_id': self.delivery_product.product_variant_id,
             'measurement_basis_id': self.shipment_basis_measure,
             'unit_price': 500,
             'currency_id': self.env.ref('base.INR'),
             'date_from': '2023/09/18',
             'date_to': '2024/09/18'}
        ]

        # Create SEA transport mode type Buy Tariff
        sea_buy_tariff_id = self.create_buy_tariff(self.export_shipment_type, self.sea_freight_mode,
                                                   self.env.ref('base.INR'), self.fcl_sea_cargo_type,
                                                   vendor_id=vendor_id,
                                                   charges=charges_dict)

        self.assertTrue(sea_buy_tariff_id)
        self.assertTrue(sea_buy_tariff_id.vendor_id)
        self.assertTrue(sea_buy_tariff_id.line_ids)
        self.assertEqual(1, len(sea_buy_tariff_id.line_ids))
        self.assertEqual('Nick-EXPSEAFCL', sea_buy_tariff_id.tariff_name)

        charges_dict = [
            {'charge_type_id': self.delivery_product.product_variant_id,
             'measurement_basis_id': self.shipment_basis_measure,
             'unit_price': 500,
             'currency_id': self.env.ref('base.INR'),
             'date_from': '2023/09/18',
             'date_to': '2024/09/18'},
            {'charge_type_id': self.main_carriage_product.product_variant_id,
             'measurement_basis_id': self.shipment_basis_measure,
             'unit_price': 200,
             'currency_id': self.env.ref('base.INR'),
             'date_from': '2023/09/18',
             'date_to': '2024/09/18'}
        ]

        # Create ROAD transport mode type Buy Tariff
        land_buy_tariff_id = self.create_buy_tariff(self.export_shipment_type, self.land_freight_mode,
                                                    self.env.ref('base.INR'), self.ftl_land_cargo_type,
                                                    vendor_id=vendor_id, charges=charges_dict)
        self.assertTrue(land_buy_tariff_id)
        self.assertTrue(land_buy_tariff_id.vendor_id)
        self.assertTrue(land_buy_tariff_id.line_ids)
        self.assertEqual(2, len(land_buy_tariff_id.line_ids))
        self.assertEqual('Nick-EXPROEFTL', land_buy_tariff_id.tariff_name)

        _logger.info("\n\n=================== Tested TC00407 test case ===================\n")

    def test_tc00415_create_buy_tariff_for_vendor_without_charges(self):
        """
        Test Case for create a new buy tariff for a vendor without adding charges.

        TC No: #TC00415
        """
        _logger.info("\n\n=================== Started TC00415 test case ===================\n")

        # Get Vendor
        vendor_id = self.setup_partner_data('Nick', company_type='person', category_ids=[self.vendor_party_type])

        # Create SEA transport mode type Buy Tariff
        sea_buy_tariff_id = self.create_buy_tariff(self.export_shipment_type, self.sea_freight_mode,
                                                   self.env.ref('base.INR'), self.fcl_sea_cargo_type,
                                                   vendor_id=vendor_id)

        self.assertTrue(sea_buy_tariff_id)
        self.assertTrue(sea_buy_tariff_id.vendor_id)
        self.assertFalse(sea_buy_tariff_id.line_ids)

        # Create ROAD transport mode type Buy Tariff
        land_buy_tariff_id = self.create_buy_tariff(self.export_shipment_type, self.land_freight_mode,
                                                    self.env.ref('base.INR'), self.ftl_land_cargo_type,
                                                    vendor_id=vendor_id)
        self.assertTrue(land_buy_tariff_id)
        self.assertTrue(land_buy_tariff_id.vendor_id)
        self.assertFalse(land_buy_tariff_id.line_ids)

        _logger.info("\n\n=================== Tested TC00415 test case ===================\n")

    def test_tc00449_add_charges_sell_tariff_from_charge_master(self):
        """
        Test Case for add charges in Sell Tariff using Fetch Charge Master.

        TC No: #TC00449
        """
        _logger.info("\n\n=================== Started TC00449 test case ===================\n")
        # Get customer
        customer_id = self.setup_partner_data('Dora', company_type='person', category_ids=[self.customer_party_type])

        # Create SEA transport mode type Sell Tariff
        sea_sell_tariff_id = self.create_sell_tariff(self.export_shipment_type, self.sea_freight_mode,
                                                     self.env.ref('base.INR'), self.fcl_sea_cargo_type,
                                                     customer_id=customer_id)

        # Create charge master wizard
        wiz_charge_master_id = self.env['wizard.charge.master.fetch'].create({
            'res_id': sea_sell_tariff_id.id,
            'res_model': 'tariff.sell',
            'company_id': sea_sell_tariff_id.company_id.id,
        })
        with Form(wiz_charge_master_id) as wiz_charge_master_form:
            wiz_charge_master_form.charge_ids.add(self.pickup_product.product_variant_id)
            wiz_charge_master_form.charge_ids.add(self.main_carriage_product.product_variant_id)

        self.assertEqual(2, len(wiz_charge_master_id.charge_ids))

        # Fetch charge master in sell tariff
        wiz_charge_master_id.action_fetch_and_override()

        self.assertEqual(2, len(sea_sell_tariff_id.line_ids))

        _logger.info("\n\n=================== Tested TC00449 test case ===================\n")

    def test_tc00454_add_charges_buy_tariff_from_charge_master(self):
        """
        Test Case for add charges in Buy Tariff using Fetch Charge Master.

        TC No: #TC00454
        """
        _logger.info("\n\n=================== Started TC00454 test case ===================\n")
        # Get Vendor
        vendor_id = self.setup_partner_data('Nick', company_type='person', category_ids=[self.vendor_party_type])

        # Create SEA transport mode type Buy Tariff
        sea_buy_tariff_id = self.create_buy_tariff(self.export_shipment_type, self.sea_freight_mode,
                                                   self.env.ref('base.INR'), self.fcl_sea_cargo_type,
                                                   vendor_id=vendor_id)

        # Create charge master wizard
        wiz_charge_master_id = self.env['wizard.charge.master.fetch'].create({
            'res_id': sea_buy_tariff_id.id,
            'res_model': 'tariff.buy',
            'company_id': sea_buy_tariff_id.company_id.id,
        })
        with Form(wiz_charge_master_id) as wiz_charge_master_form:
            wiz_charge_master_form.charge_ids.add(self.pickup_product.product_variant_id)
            wiz_charge_master_form.charge_ids.add(self.main_carriage_product.product_variant_id)

        self.assertEqual(2, len(wiz_charge_master_id.charge_ids))

        # Fetch charge master in buy tariff
        wiz_charge_master_id.action_fetch_and_override()

        self.assertEqual(2, len(sea_buy_tariff_id.line_ids))

        _logger.info("\n\n=================== Tested TC00454 test case ===================\n")

    def test_tc00456_remove_all_charges_buy_tariff(self):
        """
        Test Case for Remove all the charges of Buy Tariff.

        TC No: #TC00456
        """
        _logger.info("\n\n=================== Started TC00456 test case ===================\n")
        # Get Vendor
        vendor_id = self.setup_partner_data('Nick', company_type='person', category_ids=[self.vendor_party_type])

        # Create SEA transport mode type Buy Tariff
        sea_buy_tariff_id = self.create_buy_tariff(self.export_shipment_type, self.sea_freight_mode,
                                                   self.env.ref('base.INR'), self.fcl_sea_cargo_type,
                                                   vendor_id=vendor_id)

        # Create charge master wizard
        wiz_charge_master_id = self.env['wizard.charge.master.fetch'].create({
            'res_id': sea_buy_tariff_id.id,
            'res_model': 'tariff.buy',
            'company_id': sea_buy_tariff_id.company_id.id,
        })
        with Form(wiz_charge_master_id) as wiz_charge_master_form:
            wiz_charge_master_form.charge_ids.add(self.pickup_product.product_variant_id)
            wiz_charge_master_form.charge_ids.add(self.main_carriage_product.product_variant_id)
        self.assertEqual(2, len(wiz_charge_master_id.charge_ids))

        # Fetch charge master in buy tariff
        wiz_charge_master_id.action_fetch_and_override()

        self.assertEqual(2, len(sea_buy_tariff_id.line_ids))

        # Remove all charges from buy tariff
        sea_buy_tariff_id.action_remove_charges()
        self.assertFalse(sea_buy_tariff_id.line_ids)

        _logger.info("\n\n=================== Tested TC00456 test case ===================\n")

    def test_tc00458_remove_all_charges_sell_tariff(self):
        """
        Test Case for Remove all the charges of Sell Tariff.

        TC No: #TC00458
        """
        _logger.info("\n\n=================== Started TC00458 test case ===================\n")
        # Get customer
        customer_id = self.setup_partner_data('Dora', company_type='person', category_ids=[self.customer_party_type])

        # Create SEA transport mode type Sell Tariff
        sea_sell_tariff_id = self.create_sell_tariff(self.export_shipment_type, self.sea_freight_mode,
                                                     self.env.ref('base.INR'), self.fcl_sea_cargo_type,
                                                     customer_id=customer_id)

        # Create charge master wizard
        wiz_charge_master_id = self.env['wizard.charge.master.fetch'].create({
            'res_id': sea_sell_tariff_id.id,
            'res_model': 'tariff.sell',
            'company_id': sea_sell_tariff_id.company_id.id,
        })
        with Form(wiz_charge_master_id) as wiz_charge_master_form:
            wiz_charge_master_form.charge_ids.add(self.pickup_product.product_variant_id)
            wiz_charge_master_form.charge_ids.add(self.main_carriage_product.product_variant_id)

        self.assertEqual(2, len(wiz_charge_master_id.charge_ids))

        # Fetch charge master in sell tariff
        wiz_charge_master_id.action_fetch_and_override()
        self.assertEqual(2, len(sea_sell_tariff_id.line_ids))

        # Remove all charges from sell tariff
        sea_sell_tariff_id.action_remove_charges()
        self.assertFalse(sea_sell_tariff_id.line_ids)

        _logger.info("\n\n=================== Tested TC00458 test case ===================\n")
