# -*- coding: utf-8 -*-

import logging
from .common import FreightShipmentCommon
from odoo.tests import Form
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class TestHouseShipment(FreightShipmentCommon):

    def create_house_revenue_charges(self, house_shipment, product, currency, amount):
        """
        Create Revenue charges for the house shipment.

        @param {recordset} house_shipment: single record of 'freight.house.shipment'
        @param {recordset} product: single record of 'product.product'
        @param {recordset} currency: single record of 'res.currency'
        @param {integer} amount: amount per unit of product
        @return {recordset}: single record of 'house.shipment.charge.revenue'
        """
        house_revenue_form = Form(self.env["house.shipment.charge.revenue"])
        house_revenue_form.product_id = product
        house_revenue_form.partner_id = house_shipment.client_id
        house_revenue_form.amount_currency_id = currency
        house_revenue_form.amount_rate = amount
        house_revenue_form.house_shipment_id = house_shipment
        return house_revenue_form.save()

    def create_shipment_charge_wiz_to_single_currency_invoice(self, house_shipment, inr_currency, customer):
        """
        Create single currency invoice from the shipment charge wizard which contain multiple currencies

        @param {recordset} house_shipment: record of 'freight.house.shipment'
        @param {recordset} inr_currency: record of 'res.currency'
        @param {recordset} customer: record of 'res.partner'
        @return {recordset} move: single record of 'account.move'
        """
        # Create Generating Invoices wizard for all selected revenue charges
        invoice_wizard = self.env['shipment.charge.invoice.wizard'].create({
            'charge_ids': [(6, False, house_shipment.revenue_charge_ids.ids)],
            'house_shipment_id': house_shipment.id,
            'partner_mode': 'specific',
            'partner_ids': [(6, 0, customer.ids)],
            'single_currency_billing': True,
            'currency_id': inr_currency.id,
        })
        invoice_wizard._onchange_field_values()
        invoice_wizard._onchange_currency_id()

        # Create invoice from the Generating Invoices wizard
        invoice_dict = invoice_wizard.action_generate_invoices()
        move = self.env['account.move'].browse(invoice_dict.get('res_id'))
        return move

    def test_tc00038_multi_charge_diff_currency_to_inv_single_currency(self):
        """
        Test Case for Add multiple charges with different Currencies and
        create a revenue invoice with single currency billing
        If single invoice is created then it is single currency otherwise it will be created multiple invoice

        TC No: #TC00038
        """
        _logger.info("\n\n=================== Started TC00038 test case ===================\n")

        inr_currency = self.setup_currency_data('base.INR')
        aed_currency = self.setup_currency_data('base.AED')
        customer = self.partner_client_id

        # Create Revenue Charges
        self.create_house_revenue_charges(self.export_house_shipment, self.delivery_product.product_variant_id,
                                          inr_currency, 1000)
        self.create_house_revenue_charges(self.export_house_shipment, self.main_carriage_product.product_variant_id,
                                          aed_currency, 1050)
        self.assertEqual(len(self.export_house_shipment.revenue_charge_ids), 2)

        # Create invoice by the shipment invoice charge wizard
        move = self.create_shipment_charge_wiz_to_single_currency_invoice(self.export_house_shipment, inr_currency,
                                                                          customer)

        self.assertEqual(len(self.export_house_shipment.move_ids.ids), 1)
        self.assertEqual(move.currency_id.id, inr_currency.id)

        _logger.info("\n\n=================== Tested TC00038 test case ===================\n")

    def test_tc00078_haz_details_in_additional_tab(self):
        """
        Test Case for Verify the 'HAZ Details' of Additional tab for house shipment.

        TC No: #TC00078
        """
        _logger.info("\n\n=================== Started TC00078 test case ===================\n")

        haz_class_code = self.env.ref("freight_base.haz_class_code_class_1")

        # Check validation for required field
        with self.assertRaisesRegex(AssertionError, 'required field'):
            with Form(self.export_house_shipment) as shipment_form:
                shipment_form.is_hazardous = True

        # Enable 'Auto Update Weight & Volume' in house shipment
        with Form(self.export_house_shipment) as shipment_form:
            shipment_form.is_hazardous = True
            shipment_form.haz_class_id = haz_class_code
            shipment_form.haz_un_number = 1548

        self.assertTrue(self.export_house_shipment.is_hazardous)
        self.assertEqual('1548', self.export_house_shipment.haz_un_number)
        self.assertEqual(haz_class_code, self.export_house_shipment.haz_class_id)

        _logger.info("\n\n=================== Tested TC00078 test case ===================\n")

    def test_tc00089_add_parties_house_shipment(self):
        """
        Test Case for 'Add Parties in House Shipment by the one2many field'
        Here, we have added only 1 party, but it would be a 4 party are there
        because we have added shipper, consignee, client while create house shipment.
        So, our expected total parties are 4.

        TC No: #TC00089
        """
        _logger.info("\n\n=================== Started TC00089 test case ===================\n")

        # Add parties
        with Form(self.export_house_shipment) as house_shipment_form:
            with house_shipment_form.shipment_partner_ids.new() as shipment_partner_line:
                shipment_partner_line.partner_type_id = self.vendor_party_type
                shipment_partner_line.partner_id = self.partner_client_id

        self.assertEqual(4, len(self.export_house_shipment.shipment_partner_ids))

        _logger.info("\n\n=================== Tested TC00089 test case ===================\n")

    def test_tc00095_add_package_by_container_popup(self):
        """
        Test Case for Add Package from Create Container popup.
        Test Total weight, volume and volumetric in container based on packages.

        TC No: #TC00095
        """
        _logger.info("\n\n=================== Started TC00095 test case ===================\n")

        # Create container type
        container_type = self.setup_container_type('Twenty foot flatrack', '20FR', 2)

        # Add container in house shipment
        with Form(self.export_house_shipment) as house_shipment_form:
            with house_shipment_form.container_ids.new() as container_line:
                container_line.container_type_id = container_type

        self.assertEqual(1, len(self.export_house_shipment.container_ids))

        # Add packages type inside the container
        with Form(self.export_house_shipment.container_ids) as shipment_package_form:
            with shipment_package_form.package_group_ids.new() as package_group_line:
                package_group_line.package_type_id = self.env.ref('freight_base.pack_uom_bag')
                package_group_line.weight_unit = 123
                package_group_line.volume_unit = 12
                package_group_line.volumetric_weight = 122
            with shipment_package_form.package_group_ids.new() as package_group_line:
                package_group_line.package_type_id = self.env.ref('freight_base.pack_uom_bbg')
                package_group_line.weight_unit = 123
                package_group_line.volume_unit = 12
                package_group_line.volumetric_weight = 122

            self.assertEqual(2, len(shipment_package_form.package_group_ids))

            self.assertEqual(246, shipment_package_form.total_weight_unit)
            self.assertEqual(24, shipment_package_form.total_volume_unit)
            self.assertEqual(244, shipment_package_form.total_volumetric_weight)

        _logger.info("\n\n=================== Tested TC00095 test case ===================\n")

    def test_tc00108_remove_package_by_clicking_delete_package_button(self):
        """
        Test Case for Remove all packages from house shipment by clicking on 'Delete all Packages'.

        TC No: #TC00108
        """
        _logger.info("\n\n=================== Started TC00108 test case ===================\n")

        # Create container type
        container_20fr__type = self.setup_container_type('Twenty foot flatrack', '20FR', 2)
        container_40fr__type = self.setup_container_type('Forty foot flatrack', '40FR', 2)

        self.assertIsNotNone(container_20fr__type, 'Container 20FR should not be Null')
        self.assertIsNotNone(container_20fr__type, 'Container 40FR should not be Null')

        # Add container in house shipment
        with Form(self.export_house_shipment) as house_shipment_form:
            with house_shipment_form.container_ids.new() as container_line:
                container_line.container_type_id = container_20fr__type
            with house_shipment_form.container_ids.new() as container_line:
                container_line.container_type_id = container_40fr__type

        self.assertEqual(2, len(self.export_house_shipment.container_ids))

        # Delete all packages
        self.export_house_shipment.action_remove_all_packages()

        self.assertEqual(0, len(self.export_house_shipment.container_ids))

        _logger.info("\n\n=================== Tested TC00108 test case ===================\n")

    def test_tc00134_create_terms_nd_condition_for_documents(self):
        """
        Test Case for create Terms & Conditions for documents on level of house shipment.

        TC No: #TC00134
        """
        _logger.info("\n\n=================== Started TC00134 test case ===================\n")

        # Create term & condition in house shipment
        with Form(self.export_house_shipment) as house_shipment_form:
            with house_shipment_form.terms_ids.new() as terms_line:
                terms_line.document_type_id = self.env.ref('freight_management.doc_type_house_line_order_delivery')
                terms_line.terms_and_conditions = 'TC00134: Testing Purpose'

        self.assertEqual(1, len(self.export_house_shipment.terms_ids))

        _logger.info("\n\n=================== Tested TC00134 test case ===================\n")

    def test_tc00135_change_status_to_nomination_generated(self):
        """
        Test Case for Verify the Status "Nomination Generated" of the import type House Shipment

        TC No: #TC00135
        """
        _logger.info("\n\n=================== Started TC00135 test case ===================\n")

        # Add House BL number in house shipment
        with Form(self.import_house_shipment) as shipment_form:
            shipment_form.hbl_number = 'HBL00014'

        self.assertEqual('HBL00014', self.import_house_shipment.hbl_number)

        # Create Change Status record
        shipment_status_form = Form(self.env["wizard.house.shipment.status"])
        shipment_status_form.shipment_id = self.import_house_shipment
        shipment_status_form.import_state = self.import_house_shipment.import_state
        shipment_status_wizard = shipment_status_form.save()

        # Change status to HBL Generated
        shipment_status_wizard.import_state = 'nomination_generated'
        shipment_status_wizard.action_change_status()

        self.assertEqual('nomination_generated', self.import_house_shipment.import_state)

        _logger.info("\n\n=================== Tested TC00135 test case ===================\n")

    def test_tc00136_auto_update_package_declared_weight_nd_volume(self):
        """
        Test Case for auto update packages 'Declared Weight & Volume'.
        By adding packages inside the container, declared weight & volume should be calculated automatically

        TC No: #TC00136
        """
        _logger.info("\n\n=================== Started TC00136 test case ===================\n")

        # Enable 'Auto Update Weight & Volume' in house shipment
        with Form(self.export_house_shipment) as shipment_form:
            shipment_form.auto_update_weight_volume = True

        # Create container type
        container_type = self.setup_container_type('Twenty foot flatrack', '20FR', 2)

        # Add container in house shipment
        with Form(self.export_house_shipment) as house_shipment_form:
            with house_shipment_form.container_ids.new() as container_line:
                container_line.container_type_id = container_type

        # Add packages type inside the container
        with Form(self.export_house_shipment.container_ids) as shipment_package_form:
            with shipment_package_form.package_group_ids.new() as package_group_line:
                package_group_line.package_type_id = self.env.ref('freight_base.pack_uom_bag')
                package_group_line.weight_unit = 123
                package_group_line.volume_unit = 12
                package_group_line.volumetric_weight = 122
            with shipment_package_form.package_group_ids.new() as package_group_line:
                package_group_line.package_type_id = self.env.ref('freight_base.pack_uom_bbg')
                package_group_line.weight_unit = 123
                package_group_line.volume_unit = 12
                package_group_line.volumetric_weight = 122

        self.assertEqual(244, self.export_house_shipment.weight_volume_unit)
        self.assertEqual(24, self.export_house_shipment.volume_unit)
        self.assertEqual(246, self.export_house_shipment.gross_weight_unit)

        _logger.info("\n\n=================== Tested TC00136 test case ===================\n")

    def test_add_duplicate_container_LCL_type_house_shipment(self):
        """
        Test Case for add duplicate container in LCL type house shipment.
        result: LCL house shipment should allow duplicate container.
        """
        _logger.info(
            "\n\n=================== Started LCL Type House add duplicate containers test case ===================\n")

        # Create LCL Type House Shipment
        lcl_house_shipment = self.setup_house_shipment_data(self.export_shipment_type,
                                                            self.lcl_sea_cargo_type,
                                                            self.sea_freight_mode,
                                                            '2023-10-04', self.incoterm_EXW)

        # Create Container
        container_id = self.create_container('AOKJ1235034')

        # Add container in house shipment
        with Form(lcl_house_shipment) as house_shipment_form:
            with house_shipment_form.package_ids.new() as package_line:
                package_line.package_type_id = self.env.ref('freight_base.pack_uom_amm')
                package_line.container_number = container_id

            with house_shipment_form.package_ids.new() as package_line:
                package_line.package_type_id = self.env.ref('freight_base.pack_uom_bal')
                package_line.container_number = container_id

        self.assertTrue(lcl_house_shipment.package_ids)
        self.assertEqual(2, len(lcl_house_shipment.package_ids))
        self.assertTrue(lcl_house_shipment.package_ids[0].container_number)
        self.assertTrue(lcl_house_shipment.package_ids[1].container_number)

        _logger.info(
            "\n\n=================== Tested LCL Type House add duplicate containers test case ===================\n")

    def test_add_duplicate_container_FCL_type_house_shipment(self):
        """
        Test Case for add duplicate container in FCL type house shipment.
        result: FCL house shipment should not allow duplicate container.
        """
        _logger.info(
            "\n\n=================== Started FCL Type House add duplicate containers test case ===================\n")

        # Create Container
        container_id = self.create_container('FCIU6188472')

        # Create container type
        container_type_id = self.setup_container_type('Twenty foot flatrack', '20FR', 2)

        # Add container in house shipment
        fm_container_validation_installed = self.env['ir.module.module'].search([('state', '=', 'installed'), ('name', '=', 'fm_container_validation')])
        # Check ValidationError if fm_container_validation_installed is true
        if fm_container_validation_installed:
            with self.assertRaises(ValidationError) as Message:
                with Form(self.export_house_shipment) as house_shipment_form:
                    with house_shipment_form.container_ids.new() as container_line:
                        container_line.container_type_id = container_type_id
                        container_line.container_number = container_id
                    with house_shipment_form.container_ids.new() as container_line:
                        container_line.container_type_id = container_type_id
                        container_line.container_number = container_id

            self.assertEqual(str(Message.exception), 'Container number should be unique.')
            self.assertFalse(self.export_house_shipment.container_ids)

        else:
            with Form(self.export_house_shipment) as house_shipment_form:
                with house_shipment_form.container_ids.new() as container_line:
                    container_line.container_type_id = container_type_id
                    container_line.container_number = container_id
                with house_shipment_form.container_ids.new() as container_line:
                    container_line.container_type_id = container_type_id
                    container_line.container_number = container_id
            self.assertTrue(self.export_house_shipment.container_ids)

        _logger.info(
            "\n\n=================== Tested FCL Type House add duplicate containers test case ===================\n")

    def test_add_unique_container_FCL_type_house_shipment(self):
        """
        Test Case for add unique container in FCL type house shipment.
        result: FCL house shipment should allow unique container.
        """
        _logger.info(
            "\n\n=================== Started FCL Type House add unique containers test case ===================\n")

        # Create Container
        container_id = self.create_container('AOKJ3685895')
        container1_id = self.create_container('TLLU2980127')

        # Create container type
        container_type_id = self.setup_container_type('Twenty foot flatrack', '20FR', 2)

        # Add container in house shipment
        with Form(self.export_house_shipment) as house_shipment_form:
            with house_shipment_form.container_ids.new() as container_line:
                container_line.container_type_id = container_type_id
                container_line.container_number = container_id
            with house_shipment_form.container_ids.new() as container_line:
                container_line.container_type_id = container_type_id
                container_line.container_number = container1_id

        self.assertTrue(self.export_house_shipment.container_ids)
        self.assertEqual(2, len(self.export_house_shipment.container_ids))
        self.assertTrue(self.export_house_shipment.container_ids[0].container_number)
        self.assertTrue(self.export_house_shipment.container_ids[1].container_number)

        _logger.info(
            "\n\n=================== Tested FCL Type House add unique containers test case ===================\n")
