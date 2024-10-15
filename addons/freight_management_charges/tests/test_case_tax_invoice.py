import logging
from odoo.tests.common import TransactionCase, tagged, Form

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class TestAccountMoveLine(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.house_shipment = cls.create_house(name='HBL000TEST0001')
        cls.move_id = cls.create_invoice(house_shipment=cls.house_shipment)


    def tax_price_include(self):
        return self.env['account.tax'].create({
            'name': '10% incl',
            'type_tax_use': 'purchase',
            'amount_type': 'percent',
            'amount': 10,
            'price_include': True,
            'include_base_amount': True,
        })

    @classmethod
    def create_product(cls, name='product'):
        return cls.env['product.product'].create({
            'name': name,
            'uom_id': cls.env.ref('uom.product_uom_unit').id,
            'standard_price': 110.0,
        })

    @classmethod
    def create_house(cls, name):
        house_shipment = cls.env['freight.house.shipment'].create({
            'shipment_date': '2023-12-11',
            'booking_nomination_no': name,
            'transport_mode_id': cls.env.ref('freight_base.transport_mode_sea').id,
            'shipment_type_id': cls.env.ref('freight_base.shipment_type_import').id,
            'cargo_type_id': cls.env.ref('freight_base.cargo_type_sea_fcl').id,
            'inco_term_id': cls.env.ref('account.incoterm_EXW').id,
            'service_mode_id': cls.env.ref('freight_base.service_mode_d2p').id,
            'client_id': cls.env.ref('base.user_admin').id,
            'shipper_id': cls.env.ref('base.user_admin').id,
            'consignee_id': cls.env.ref('base.user_admin').id,
        })
        cls.env['house.shipment.charge.revenue'].create([{
            'house_shipment_id': house_shipment and house_shipment.id or False,
            'product_id': cls.env.ref('freight_base.product_template_delivery').id,
            'charge_description': ' delivery 1',
            'partner_id': cls.env.ref('base.partner_admin').id,
            'measurement_basis_id': cls.env.ref('freight_base.measurement_basis_shipment').id,
            'quantity': 1,
            'amount_currency_id': cls.env.ref('base.INR').id,
            'amount_rate': 100,
            'amount_conversion_rate': 1,
            'total_currency_amount': 100,
            'total_amount': 100,
        },
            {
                'house_shipment_id': house_shipment and house_shipment.id or False,
                'product_id': cls.env.ref('freight_base.product_template_delivery').id,
                'charge_description': 'delivery',
                'partner_id': cls.env.ref('base.partner_admin').id,
                'measurement_basis_id': cls.env.ref('freight_base.measurement_basis_shipment').id,
                'quantity': 1,
                'amount_currency_id': cls.env.ref('base.INR').id,
                'amount_rate': 200,
                'amount_conversion_rate': 1,
                'total_currency_amount': 200,
                'total_amount': 200,
            },

            {
                'house_shipment_id': house_shipment and house_shipment.id or False,
                'product_id': cls.env.ref('freight_base.product_template_pickup').id,
                'charge_description': 'pickup',
                'partner_id': cls.env.ref('base.user_admin').id,
                'measurement_basis_id': cls.env.ref('freight_base.measurement_basis_shipment').id,
                'quantity': 1,
                'amount_currency_id': cls.env.ref('base.INR').id,
                'amount_rate': 200,
                'amount_conversion_rate': 1,
                'total_currency_amount': 200,
                'total_amount': 200,
            }
        ])
        return house_shipment

    @classmethod
    def create_invoice(cls, house_shipment):

        invoice_wizard = cls.env['shipment.charge.invoice.wizard'].create({
            'charge_ids': [(6, False, house_shipment.revenue_charge_ids.ids)],
            'house_shipment_id': house_shipment.id,
            'partner_mode': 'specific',
            'partner_ids': [(6, 0, [cls.env.ref('base.partner_admin').id])],
            'single_currency_billing': True,
            'currency_id': cls.env.ref('base.INR').id,
        })
        invoice_wizard._onchange_field_values()
        invoice_wizard._onchange_currency_id()
        invoice_dict = invoice_wizard.action_generate_invoices()
        move_id = cls.env['account.move'].browse(invoice_dict.get('res_id'))
        move_id.get_invoice_line_for_document(['house_shipment_id'])
        seq = 5
        for line in move_id.invoice_line_ids:
            line.sequence = seq
            seq += 5
        return move_id

    def test_01_tax_invoice_with_house_and_without_section(self):
        """
        Invoice created with house and added a single section in the house.
        """
        _logger.info(
                "\n\n=================== Started 01 test case With House and without section and Note !===================\n")
        # house_shipment = self.create_house('HBL000TEST0001')
        # move_id = self.create_invoice(house_shipment)
        invoice_line_disc = self.move_id.get_invoice_line_for_document(['house_shipment_id'])
        lines_disc = [
            {
                'product_id': 'Desk Stand with Screen',
                'name': '[FURN_7888] Desk Stand with Screen- delivery 1',
                'quantity': 1.0,
                'currency_id': 'INR',
                'currency_exchange_rate': '',
                'price_unit': 100.0,
                'FCY_Amt': ' 100.00',
                'vat': ' 0.00',
                'Amount': ' 100.00',
                'house_shipment_id': self.house_shipment.name,
                'service_job_id': '',
                'unit': '',
                'display_type': '',
                'sequence': 5,
                'tax_ids': ''
            },
            {
                'product_id': 'Desk Stand with Screen',
                'name': '[FURN_7888] Desk Stand with Screen-delivery',
                'quantity': 1.0,
                'currency_id': 'INR',
                'currency_exchange_rate': '',
                'price_unit': 200.0,
                'FCY_Amt': ' 200.00',
                'vat': ' 0.00',
                'Amount': ' 200.00',
                'house_shipment_id': self.house_shipment.name,
                'service_job_id': '',
                'unit': '',
                'display_type': '',
                'sequence': 6,
                'tax_ids': ''
            }
        ]
        self.assertListEqual(lines_disc, invoice_line_disc[0].get('lines'))

        _logger.info(
            "\n\n=================== Test 01 with house and without section and Note complated sucessfully..! ===================\n")

    def test_02_tax_invoice_with__house_and_with_section(self):
        """
        Single house invoice created and added two section added after house invoice line and before without a house invoice line.
        """
        _logger.info(
            "\n\n=================== Started 02 test case With House and with section and Note !===================\n")
        move_id = self.move_id
        invoice_line_disc = move_id.get_invoice_line_for_document(['house_shipment_id'])
        self.env['account.move.line'].create([
            {
                'display_type': 'line_section',
                'name': 'This is a section',
                'account_id': False,
                'move_id': move_id.id,
                'sequence': 1,
            },
            {
                'display_type': 'line_note',
                'name': 'This is a note',
                'account_id': False,
                'move_id': move_id.id,
                'sequence': 20
            }])
        invoice_line_disc = move_id.get_invoice_line_for_document(['house_shipment_id'])
        lines_disc = [{
            'product_id': '',
            'name': 'This is a section',
            'quantity': 1.0,
            'currency_id': 'INR',
            'currency_exchange_rate': '',
            'price_unit': '',
            'FCY_Amt': ' 0.00',
            'vat': ' 0.00',
            'Amount': ' 0.00',
            'house_shipment_id': '',
            'service_job_id': '',
            'unit': '',
            'display_type': 'line_section',
            'sequence': 1,
            'tax_ids': ''
        },
            {
                'product_id': 'Desk Stand with Screen',
                'name': '[FURN_7888] Desk Stand with Screen- delivery 1',
                'quantity': 1.0,
                'currency_id': 'INR',
                'currency_exchange_rate': '',
                'price_unit': 100.0,
                'FCY_Amt': ' 100.00',
                'vat': ' 0.00',
                'Amount': ' 100.00',
                'house_shipment_id': self.house_shipment.name,
                'service_job_id': '',
                'unit': '',
                'display_type': '',
                'sequence': 2,
                'tax_ids': ''
            },
            {
                'product_id': 'Desk Stand with Screen',
                'name': '[FURN_7888] Desk Stand with Screen-delivery',
                'quantity': 1.0,
                'currency_id': 'INR',
                'currency_exchange_rate': '',
                'price_unit': 200.0,
                'FCY_Amt': ' 200.00',
                'vat': ' 0.00',
                'Amount': ' 200.00',
                'house_shipment_id': self.house_shipment.name,
                'service_job_id': '',
                'unit': '',
                'display_type': '',
                'sequence': 3,
                'tax_ids': ''
            },
            {
                'product_id': '',
                'name': 'This is a note',
                'quantity': 1.0,
                'currency_id': 'INR',
                'currency_exchange_rate': '',
                'price_unit': '',
                'FCY_Amt': ' 0.00',
                'vat': ' 0.00',
                'Amount': ' 0.00',
                'house_shipment_id': '',
                'service_job_id': '',
                'unit': '',
                'display_type': 'line_note',
                'sequence': 4,
                'tax_ids': ''
            }]
        self.assertListEqual(lines_disc, invoice_line_disc[0].get('lines'))
        _logger.info(
            "\n\n=================== Test 02 with house and with section and Note complated sucessfully..! ===================\n")

    def test_03_tax_invoice_with__house_and_with_two_section(self):
        """
        - Two section added in invoice and in between two section added house invoice line, without house invoice line and note.
        - Section added in invoice line.
        - Note added after with house invoice line.
        """
        move_id = self.move_id
        _logger.info(
            "\n\n=================== Started 03 test case With House and with two section and Note !===================\n")
        self.env['account.move.line'].create([
            {
                'display_type': 'line_section',
                'name': 'This is a section',
                'account_id': False,
                'move_id': move_id.id,
                'sequence': 1,
            },
            {
                'display_type': 'line_note',
                'name': 'This is a note',
                'account_id': False,
                'move_id': move_id.id,
                'sequence': 20
            },
            {
                'display_type': 'line_section',
                'name': 'This is a section',
                'account_id': False,
                'move_id': move_id.id,
                'sequence': 7,
            },
            {
                'display_type': 'line_note',
                'name': 'This is a note 2',
                'account_id': False,
                'move_id': move_id.id,
                'sequence': 6
            }])
        invoice_line_disc = move_id.get_invoice_line_for_document(['house_shipment_id'])
        lines_disc = [
            {
                'product_id': '',
                'name': 'This is a section',
                'quantity': 1.0,
                'currency_id': 'INR',
                'currency_exchange_rate': '',
                'price_unit': '',
                'FCY_Amt': ' 0.00',
                'vat': ' 0.00',
                'Amount': ' 0.00',
                'house_shipment_id': '',
                'service_job_id': '',
                'unit': '',
                'display_type': 'line_section',
                'sequence': 1,
                'tax_ids': ''
            },
            {
                'product_id': 'Desk Stand with Screen',
                'name': '[FURN_7888] Desk Stand with Screen- delivery 1',
                'quantity': 1.0,
                'currency_id': 'INR',
                'currency_exchange_rate': '',
                'price_unit': 100.0,
                'FCY_Amt': ' 100.00',
                'vat': ' 0.00',
                'Amount': ' 100.00',
                'house_shipment_id': self.house_shipment.name,
                'service_job_id': '',
                'unit': '',
                'display_type': '',
                'sequence': 2,
                'tax_ids': ''
            },
            {
                'product_id': '',
                'name': 'This is a note 2',
                'quantity': 1.0,
                'currency_id': 'INR',
                'currency_exchange_rate': '',
                'price_unit': '',
                'FCY_Amt': ' 0.00',
                'vat': ' 0.00',
                'Amount': ' 0.00',
                'house_shipment_id': '',
                'service_job_id': '',
                'unit': '',
                'display_type': 'line_note',
                'sequence': 3,
                'tax_ids': ''
            },
            {
                'product_id': '',
                'name': 'Total',
                'quantity': 0,
                'currency_id': '',
                'currency_exchange_rate': '',
                'price_unit': '',
                'FCY_Amt': '0.0',
                'vat': '',
                'Amount': ' 100.00',
                'house_shipment_id': '',
                'service_job_id': '',
                'unit': '',
                'display_type': 'line_section_total',
                'sequence': 4,
                'tax_ids': ''
            },
            {
                'product_id': '',
                'name': 'This is a section',
                'quantity': 1.0,
                'currency_id': 'INR',
                'currency_exchange_rate': '',
                'price_unit': '',
                'FCY_Amt': ' 0.00',
                'vat': ' 0.00',
                'Amount': ' 0.00',
                'house_shipment_id': '',
                'service_job_id': '',
                'unit': '',
                'display_type': 'line_section',
                'sequence': 5,
                'tax_ids': ''
            },
            {
                'product_id': 'Desk Stand with Screen',
                'name': '[FURN_7888] Desk Stand with Screen-delivery',
                'quantity': 1.0,
                'currency_id': 'INR',
                'currency_exchange_rate': '',
                'price_unit': 200.0,
                'FCY_Amt': ' 200.00',
                'vat': ' 0.00',
                'Amount': ' 200.00',
                'house_shipment_id': self.house_shipment.name,
                'service_job_id': '',
                'unit': '',
                'display_type': '',
                'sequence': 6,
                'tax_ids': ''
            },
            {
                'product_id': '',
                'name': 'This is a note',
                'quantity': 1.0,
                'currency_id': 'INR',
                'currency_exchange_rate': '',
                'price_unit': '',
                'FCY_Amt': ' 0.00',
                'vat': ' 0.00',
                'Amount': ' 0.00',
                'house_shipment_id': '',
                'service_job_id': '',
                'unit': '',
                'display_type': 'line_note',
                'sequence': 7,
                'tax_ids': ''
            },
            {
                'product_id': '',
                'name': 'Total',
                'quantity': 0,
                'currency_id': '',
                'currency_exchange_rate': '',
                'price_unit': '',
                'FCY_Amt': '0.0',
                'vat': '',
                'Amount': ' 200.00',
                'house_shipment_id': '',
                'service_job_id': '',
                'unit': '',
                'display_type': 'line_section_total',
                'sequence': 8,
                'tax_ids': ''
            }]

        self.assertListEqual(lines_disc, invoice_line_disc[0].get('lines'))

        _logger.info(
            "\n\n=================== Test 03 with house and with two section and Note complated sucessfully..! ===================\n")

    def test_04_tax_invoice_with__house_section_and_orphan_charges(self):
        """
        - Note added between with house invoice line and without house invoice line (orphan charges).

        """
        _logger.info(
            "\n\n=================== Started 04 test case With House with two section,Note and orphan charges !===================\n")

        product = self.create_product('Test Product 1')
        move_id =  self.move_id
        self.move_id.invoice_line_ids += self.env['account.move.line'].new({
            'currency_id': self.ref('base.INR'),
            'sequence': 12,
            'name': product.name,
            'product_id': product.id,
            'product_uom_id': product.uom_id.id,
            'quantity': 1,
            'price_unit': 100,
            'price_subtotal': 100,
            'move_id': move_id.id,
        })
        self.env['account.move.line'].create([
         {
                'display_type': 'line_section',
                'name': 'This is a section',
                'account_id': False,
                'move_id': move_id.id,
                'sequence': 1,
            },
            {
                'display_type': 'line_note',
                'name': 'This is a note',
                'account_id': False,
                'move_id': move_id.id,
                'sequence': 20
            },
            {
                'display_type': 'line_section',
                'name': 'This is a section',
                'account_id': False,
                'move_id': move_id.id,
                'sequence': 7,
            },
            {
                'display_type': 'line_note',
                'name': 'This is a note 2',
                'account_id': False,
                'move_id': move_id.id,
                'sequence': 6
            }]
        )
        invoice_line_disc = self.move_id.get_invoice_line_for_document(['house_shipment_id'])
        lines_disc = [
            {
                'product_id': '',
                'name': 'This is a section',
                'quantity': 1.0,
                'currency_id': 'INR',
                'currency_exchange_rate': '',
                'price_unit': '',
                'FCY_Amt': ' 0.00',
                'vat': ' 0.00',
                'Amount': ' 0.00',
                'house_shipment_id': '',
                'service_job_id': '',
                'unit': '',
                'display_type': 'line_section',
                'sequence': 1,
                'tax_ids': ''
            },
            {
                'product_id': 'Desk Stand with Screen',
                'name': '[FURN_7888] Desk Stand with Screen- delivery 1',
                'quantity': 1.0,
                'currency_id': 'INR',
                'currency_exchange_rate': '',
                'price_unit': 100.0,
                'FCY_Amt': ' 100.00',
                'vat': ' 0.00',
                'Amount': ' 100.00',
                'house_shipment_id': self.house_shipment.name,
                'service_job_id': '',
                'unit': '',
                'display_type': '',
                'sequence': 2,
                'tax_ids': ''
            },
            {
                'product_id': '',
                'name': 'This is a note 2',
                'quantity': 1.0,
                'currency_id': 'INR',
                'currency_exchange_rate': '',
                'price_unit': '',
                'FCY_Amt': ' 0.00',
                'vat': ' 0.00',
                'Amount': ' 0.00',
                'house_shipment_id': '',
                'service_job_id': '',
                'unit': '',
                'display_type': 'line_note',
                'sequence': 3,
                'tax_ids': ''
            },
            {
                'product_id': '',
                'name': 'Total',
                'quantity': 0,
                'currency_id': '',
                'currency_exchange_rate': '',
                'price_unit': '',
                'FCY_Amt': '0.0',
                'vat': '',
                'Amount': ' 100.00',
                'house_shipment_id': '',
                'service_job_id': '',
                'unit': '',
                'display_type': 'line_section_total',
                'sequence': 4,
                'tax_ids': ''
            },
            {
                'product_id': '',
                'name': 'This is a section',
                'quantity': 1.0,
                'currency_id': 'INR',
                'currency_exchange_rate': '',
                'price_unit': '',
                'FCY_Amt': ' 0.00',
                'vat': ' 0.00',
                'Amount': ' 0.00',
                'house_shipment_id': '',
                'service_job_id': '',
                'unit': '',
                'display_type': 'line_section',
                'sequence': 5,
                'tax_ids': ''
            },
            {
                'product_id': 'Desk Stand with Screen',
                'name': '[FURN_7888] Desk Stand with Screen-delivery',
                'quantity': 1.0,
                'currency_id': 'INR',
                'currency_exchange_rate': '',
                'price_unit': 200.0,
                'FCY_Amt': ' 200.00',
                'vat': ' 0.00',
                'Amount': ' 200.00',
                'house_shipment_id': self.house_shipment.name,
                'service_job_id': '',
                'unit': '',
                'display_type': '',
                'sequence': 6,
                'tax_ids': ''
            },
            {
                'product_id': 'Test Product 1',
                'name': 'Test Product 1',
                'quantity': 1.0,
                'currency_id': 'INR',
                'currency_exchange_rate': '',
                'price_unit': 100.0,
                'FCY_Amt': ' 100.00',
                'vat': ' 0.00',
                'Amount': ' 100.00',
                'house_shipment_id': '',
                'service_job_id': '',
                'unit': '',
                'display_type': '',
                'sequence': 7,
                'tax_ids': ''
            },
            {
                'product_id': '',
                'name': 'This is a note',
                'quantity': 1.0,
                'currency_id': 'INR',
                'currency_exchange_rate': '',
                'price_unit': '',
                'FCY_Amt': ' 0.00',
                'vat': ' 0.00',
                'Amount': ' 0.00',
                'house_shipment_id': '',
                'service_job_id': '',
                'unit': '',
                'display_type': 'line_note',
                'sequence': 8,
                'tax_ids': ''
            },
            {
                'product_id': '',
                'name': 'Total',
                'quantity': 0,
                'currency_id': '',
                'currency_exchange_rate': '',
                'price_unit': '',
                'FCY_Amt': '0.0',
                'vat': '',
                'Amount': ' 300.00',
                'house_shipment_id': '',
                'service_job_id': '',
                'unit': '',
                'display_type': 'line_section_total',
                'sequence': 9,
                'tax_ids': ''
            }
        ]
        self.assertListEqual(lines_disc, invoice_line_disc[0].get('lines'))

        _logger.info("\n\n=================== Test 04 with house with two section, Note and orphan charges complated sucessfully..! ===================\n")

    def test_05_tax_invoice_without_house(self):
        """
        Invoice without house created without section.
        An invoice without house has been created and a section and note have been added to the invoice line.
        """
        tax_price_exclude = self.env['account.tax'].create({
            'name': '15% excl',
            'type_tax_use': 'purchase',
            'amount_type': 'percent',
            'amount': 15,
        })

        _logger.info(
            "\n\n=================== Started 05 test case Withous House section !===================\n")

        move_id = self.env['account.move'].new({
            'partner_id': self.env.ref('base.partner_admin').id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.create_product('Test Product 3').id,
                'name': 'Test Product 3',
                'price_unit': 200.0,
                'price_subtotal': 200.0,
                'price_total': 230.0,
                'tax_ids': tax_price_exclude.ids,
                'tax_line_id': False,
                'currency_id': self.env.ref('base.INR').id,
                'amount_currency': 200.0}),
                                 (0, 0, {
                                     'product_id': self.create_product('Test Product 4').id,
                                     'name': 'Test Product 4',
                                     'price_unit': 30.0,
                                     'price_subtotal': 30.0,
                                     'price_total': 30.0,
                                     'tax_ids': [],
                                     'tax_line_id': tax_price_exclude.id,
                                     'currency_id': self.env.ref('base.INR').id,
                                     'amount_currency': 30.0,
                                 }),
                                 (0, 0, {
                                     'product_id': self.create_product('Test Product 5'),
                                     'name': 'Test Product 5',
                                     'price_unit': 230.0,
                                     'price_subtotal': 230.0,
                                     'price_total': 230.0,
                                     'tax_ids': [],
                                     'tax_line_id': False,
                                     'currency_id': self.env.ref('base.INR'),
                                     'amount_currency': -230.0,
                                 })
                                 ]})



        lines_disc = [
            {
                'product_id': 'Test Product 3',
                'name': 'Test Product 3',
                'quantity': 1.0,
                'currency_id': 'INR',
                'currency_exchange_rate': '',
                'price_unit': 200.0,
                'FCY_Amt': ' 200.00',
                'vat': ' 30.00',
                'Amount': ' 200.00',
                'house_shipment_id': '',
                'service_job_id': '',
                'unit': '',
                'display_type': '',
                'sequence': 10,
                'tax_ids': ''
            },
            {
                'product_id': 'Test Product 4',
                'name': 'Test Product 4',
                'quantity': 1.0,
                'currency_id': 'INR',
                'currency_exchange_rate': '',
                'price_unit': 30.0,
                'FCY_Amt': ' 30.00',
                'vat': ' 0.00',
                'Amount': ' 30.00',
                'house_shipment_id': '',
                'service_job_id': '',
                'unit': '',
                'display_type': '',
                'sequence': 11,
                'tax_ids': ''
            },
            {
                'product_id': 'Test Product 5',
                'name': 'Test Product 5',
                'quantity': 1.0,
                'currency_id': 'INR',
                'currency_exchange_rate': '',
                'price_unit': 230.0,
                'FCY_Amt': ' 230.00',
                'vat': ' 0.00',
                'Amount': ' 230.00',
                'house_shipment_id': '',
                'service_job_id': '',
                'unit': '',
                'display_type': '',
                'sequence': 12,
                'tax_ids': ''
            }]
        invoice_line_disc = move_id.get_invoice_line_for_document(['house_shipment_id'])
        self.assertListEqual(lines_disc, invoice_line_disc[0].get('lines'))
        _logger.info(
            "\n\n=================== Test 05 without house section, Note complated sucessfully..! ===================\n")

        _logger.info(
            "\n\n=================== Started 06 test case Without House and with Section Note !===================\n")

        move_id.invoice_line_ids += self.env['account.move.line'].new(
            {
                'display_type': 'line_section',
                'name': 'This is a section',
                'account_id': False,
                'move_id': move_id.id,
                'sequence': 1,
            })
        move_id.invoice_line_ids += self.env['account.move.line'].new(
            {
                'display_type': 'line_note',
                'name': 'This is a note',
                'account_id': False,
                'move_id': move_id.id,
                'sequence': 20
            })

        invoice_line_disc = move_id.get_invoice_line_for_document(['house_shipment_id'])
        lines_disc = [
            {
                'product_id': '',
                'name': 'This is a section',
                'quantity': 1.0,
                'currency_id': '',
                'currency_exchange_rate': '',
                'price_unit': '',
                'FCY_Amt': ' 0.00',
                'vat': ' 0.00',
                'Amount': ' 0.00',
                'house_shipment_id': '',
                'service_job_id': '',
                'unit': '',
                'display_type': 'line_section',
                'sequence': 1,
                'tax_ids': ''
            },
            {
                'product_id': 'Test Product 3',
                'name': 'Test Product 3',
                'quantity': 1.0,
                'currency_id': 'INR',
                'currency_exchange_rate': '',
                'price_unit': 200.0,
                'FCY_Amt': ' 200.00',
                'vat': ' 30.00',
                'Amount': ' 200.00',
                'house_shipment_id': '',
                'service_job_id': '',
                'unit': '',
                'display_type': '',
                'sequence': 2,
                'tax_ids': ''
            },
            {
                'product_id': 'Test Product 4',
                'name': 'Test Product 4',
                'quantity': 1.0,
                'currency_id': 'INR',
                'currency_exchange_rate': '',
                'price_unit': 30.0,
                'FCY_Amt': ' 30.00',
                'vat': ' 0.00',
                'Amount': ' 30.00',
                'house_shipment_id': '',
                'service_job_id': '',
                'unit': '',
                'display_type': '',
                'sequence': 3,
                'tax_ids': ''
            },
            {
                'product_id': 'Test Product 5',
                'name': 'Test Product 5',
                'quantity': 1.0,
                'currency_id': 'INR',
                'currency_exchange_rate': '',
                'price_unit': 230.0,
                'FCY_Amt': ' 230.00',
                'vat': ' 0.00',
                'Amount': ' 230.00',
                'house_shipment_id': '',
                'service_job_id': '',
                'unit': '',
                'display_type': '',
                'sequence': 4,
                'tax_ids': ''
            },
            {
                'product_id': '',
                'name': 'This is a note',
                'quantity': 1.0,
                'currency_id': '',
                'currency_exchange_rate': '',
                'price_unit': '',
                'FCY_Amt': ' 0.00',
                'vat': ' 0.00',
                'Amount': ' 0.00',
                'house_shipment_id': '',
                'service_job_id': '',
                'unit': '',
                'display_type': 'line_note',
                'sequence': 5,
                'tax_ids': ''
            }]
        self.assertListEqual(lines_disc, invoice_line_disc[0].get('lines'))
        _logger.info(
            "\n\n=================== Test 06 without house and with Section Note complated sucessfully..! ===================\n")

    def test_07_with_two_house_tax_invoice(self):
        """
        - Second house added in invoice line.
        - Section added before second house line.
        - Second section line added in single House charge, show total line before section section
        """
        _logger.info(
            "\n\n=================== Started 07 test case With two House !===================\n")

        house_shipment_1 = self.create_house('HBL000TEST0002')
        house_shipment_2 = self.create_house('HBL000TEST0003')
        all_house = [house_shipment_1, house_shipment_2]
        move_id = self.env['account.move'].create({
            'partner_id': self.ref('base.partner_admin'),
            'add_charges_from': 'house',
            'charge_house_shipment_ids': [(6, 0, [house_shipment_1.id, house_shipment_2.id])],
            'move_type': 'out_invoice',
        })
        move_id.add_charges_from_house_shipment()

        seq = 5
        for line in move_id.invoice_line_ids.sorted(key=lambda l: l.id):
            line.sequence = seq
            seq += 5
        invoice_line_disc = move_id.get_invoice_line_for_document(['house_shipment_id'])
        lines_disc = [
            {
                'id': house_shipment_1.id,
                'name': house_shipment_1.name,
                'total_amount': ' 300.00',
                'total_amount_in_words': 'Three Hundred Rupees Only',
                'total_vat': ' 0.00',
                'lines': [
                    {
                        'product_id': 'Desk Stand with Screen',
                        'name': '[FURN_7888] Desk Stand with Screen- delivery 1',
                        'quantity': 1.0,
                        'currency_id': 'INR',
                        'currency_exchange_rate': '',
                        'price_unit': 100.0,
                        'FCY_Amt': ' 100.00',
                        'vat': ' 0.00',
                        'Amount': ' 100.00',
                        'house_shipment_id': house_shipment_1.name,
                        'service_job_id': '',
                        'unit': '',
                        'display_type': '',
                        'sequence': 5,
                        'tax_ids': ''
                    },
                    {
                        'product_id': 'Desk Stand with Screen',
                        'name': '[FURN_7888] Desk Stand with Screen-delivery',
                        'quantity': 1.0,
                        'currency_id': 'INR',
                        'currency_exchange_rate': '',
                        'price_unit': 200.0,
                        'FCY_Amt': ' 200.00',
                        'vat': ' 0.00',
                        'Amount': ' 200.00',
                        'house_shipment_id': house_shipment_1.name,
                        'service_job_id': '',
                        'unit': '',
                        'display_type': '',
                        'sequence': 6,
                        'tax_ids': ''
                    }
                ]
            },
            {
                'id': house_shipment_2.id,
                'name': house_shipment_2.name,
                'total_amount': ' 300.00',
                'total_amount_in_words': 'Three Hundred Rupees Only',
                'total_vat': ' 0.00',
                'lines': [
                    {
                        'product_id': 'Desk Stand with Screen',
                        'name': '[FURN_7888] Desk Stand with Screen- delivery 1',
                        'quantity': 1.0,
                        'currency_id': 'INR',
                        'currency_exchange_rate': '',
                        'price_unit': 100.0,
                        'FCY_Amt': ' 100.00',
                        'vat': ' 0.00',
                        'Amount': ' 100.00',
                        'house_shipment_id': house_shipment_2.name,
                        'service_job_id': '',
                        'unit': '',
                        'display_type': '',
                        'sequence': 15,
                        'tax_ids': ''
                    },
                    {
                        'product_id': 'Desk Stand with Screen',
                        'name': '[FURN_7888] Desk Stand with Screen-delivery',
                        'quantity': 1.0,
                        'currency_id': 'INR',
                        'currency_exchange_rate': '',
                        'price_unit': 200.0,
                        'FCY_Amt': ' 200.00',
                        'vat': ' 0.00',
                        'Amount': ' 200.00',
                        'house_shipment_id': house_shipment_2.name,
                        'service_job_id': '',
                        'unit': '',
                        'display_type': '',
                        'sequence': 16,
                        'tax_ids': ''
                    }
                ]
            }
        ]
        self.assertListEqual(lines_disc, invoice_line_disc)
        _logger.info(
            "\n\n=================== Test 07 with two house complated sucessfully..! ===================\n")

        _logger.info(
            "\n\n=================== Started 08 test case With two House and Section , Note !===================\n")
        self.env['account.move.line'].create([
            {
                'display_type': 'line_section',
                'name': 'This is a section',
                'account_id': False,
                'move_id': move_id.id,
                'sequence': 1,
            },
            {
                'display_type': 'line_note',
                'name': 'This is a note',
                'account_id': False,
                'move_id': move_id.id,
                'sequence': 20
            }])
        invoice_line_disc = move_id.get_invoice_line_for_document(['house_shipment_id'])
        lines_disc = [
            {
                'id': house_shipment_1.id,
                'name': house_shipment_1.name,
                'total_amount': ' 300.00',
                'total_amount_in_words': 'Three Hundred Rupees Only',
                'total_vat': ' 0.00',
                'lines': [
                    {
                        'product_id': '',
                        'name': 'This is a section',
                        'quantity': 1.0,
                        'currency_id': 'INR',
                        'currency_exchange_rate': '',
                        'price_unit': '',
                        'FCY_Amt': ' 0.00',
                        'vat': ' 0.00',
                        'Amount': ' 0.00',
                        'house_shipment_id': '',
                        'service_job_id': '',
                        'unit': '',
                        'display_type': 'line_section',
                        'sequence': 1,
                        'tax_ids': ''
                    },
                    {
                        'product_id': 'Desk Stand with Screen',
                        'name': '[FURN_7888] Desk Stand with Screen- delivery 1',
                        'quantity': 1.0,
                        'currency_id': 'INR',
                        'currency_exchange_rate': '',
                        'price_unit': 100.0,
                        'FCY_Amt': ' 100.00',
                        'vat': ' 0.00',
                        'Amount': ' 100.00',
                        'house_shipment_id': house_shipment_1.name,
                        'service_job_id': '',
                        'unit': '',
                        'display_type': '',
                        'sequence': 2,
                        'tax_ids': ''
                    },
                    {
                        'product_id': 'Desk Stand with Screen',
                        'name': '[FURN_7888] Desk Stand with Screen-delivery',
                        'quantity': 1.0,
                        'currency_id': 'INR',
                        'currency_exchange_rate': '',
                        'price_unit': 200.0,
                        'FCY_Amt': ' 200.00',
                        'vat': ' 0.00',
                        'Amount': ' 200.00',
                        'house_shipment_id': house_shipment_1.name,
                        'service_job_id': '',
                        'unit': '',
                        'display_type': '',
                        'sequence': 3,
                        'tax_ids': ''
                    }
                ]
            },
            {
                'id': house_shipment_2.id,
                'name': house_shipment_2.name,
                'total_amount': ' 300.00',
                'total_amount_in_words': 'Three Hundred Rupees Only',
                'total_vat': ' 0.00',
                'lines': [
                    {
                        'product_id': 'Desk Stand with Screen',
                        'name': '[FURN_7888] Desk Stand with Screen- delivery 1',
                        'quantity': 1.0,
                        'currency_id': 'INR',
                        'currency_exchange_rate': '',
                        'price_unit': 100.0,
                        'FCY_Amt': ' 100.00',
                        'vat': ' 0.00',
                        'Amount': ' 100.00',
                        'house_shipment_id': house_shipment_2.name,
                        'service_job_id': '',
                        'unit': '',
                        'display_type': '',
                        'sequence': 15,
                        'tax_ids': ''
                    },
                    {
                        'product_id': 'Desk Stand with Screen',
                        'name': '[FURN_7888] Desk Stand with Screen-delivery',
                        'quantity': 1.0,
                        'currency_id': 'INR',
                        'currency_exchange_rate': '',
                        'price_unit': 200.0,
                        'FCY_Amt': ' 200.00',
                        'vat': ' 0.00',
                        'Amount': ' 200.00',
                        'house_shipment_id': house_shipment_2.name,
                        'service_job_id': '',
                        'unit': '',
                        'display_type': '',
                        'sequence': 16,
                        'tax_ids': ''
                    },
                    {
                        'product_id': '',
                        'name': 'This is a note',
                        'quantity': 1.0,
                        'currency_id': 'INR',
                        'currency_exchange_rate': '',
                        'price_unit': '',
                        'FCY_Amt': ' 0.00',
                        'vat': ' 0.00',
                        'Amount': ' 0.00',
                        'house_shipment_id': '',
                        'service_job_id': '',
                        'unit': '',
                        'display_type': 'line_note',
                        'sequence': 17,
                        'tax_ids': ''
                    }
                ]
            }
        ]
        self.assertListEqual(lines_disc, invoice_line_disc)
        _logger.info(
            "\n\n=================== Test 08 with two house section, Note complated sucessfully..! ===================\n")
        _logger.info(
            "\n\n=================== Started 09 test case With two House Section and Note !===================\n")
        self.env['account.move.line'].create([
            {
                'display_type': 'line_section',
                'name': 'This is a section',
                'account_id': False,
                'move_id': move_id.id,
                'sequence': 8,
            },
            {
                'display_type': 'line_note',
                'name': 'This is a note 2',
                'account_id': False,
                'move_id': move_id.id,
                'sequence': 7
            }])

        invoice_line_disc = move_id.get_invoice_line_for_document(['house_shipment_id'])
        lines_disc = [
            {
                'id': house_shipment_1.id,
                'name': house_shipment_1.name,
                'total_amount': ' 300.00',
                'total_amount_in_words': 'Three Hundred Rupees Only',
                'total_vat': ' 0.00',
                'lines': [
                    {
                        'product_id': '',
                        'name': 'This is a section',
                        'quantity': 1.0,
                        'currency_id': 'INR',
                        'currency_exchange_rate': '',
                        'price_unit': '',
                        'FCY_Amt': ' 0.00',
                        'vat': ' 0.00',
                        'Amount': ' 0.00',
                        'house_shipment_id': '',
                        'service_job_id': '',
                        'unit': '',
                        'display_type': 'line_section',
                        'sequence': 1,
                        'tax_ids': ''
                    },
                    {
                        'product_id': 'Desk Stand with Screen',
                        'name': '[FURN_7888] Desk Stand with Screen- delivery 1',
                        'quantity': 1.0,
                        'currency_id': 'INR',
                        'currency_exchange_rate': '',
                        'price_unit': 100.0,
                        'FCY_Amt': ' 100.00',
                        'vat': ' 0.00',
                        'Amount': ' 100.00',
                        'house_shipment_id': house_shipment_1.name,
                        'service_job_id': '',
                        'unit': '',
                        'display_type': '',
                        'sequence': 2,
                        'tax_ids': ''
                    },
                    {
                        'product_id': '',
                        'name': 'This is a note 2',
                        'quantity': 1.0,
                        'currency_id': 'INR',
                        'currency_exchange_rate': '',
                        'price_unit': '',
                        'FCY_Amt': ' 0.00',
                        'vat': ' 0.00',
                        'Amount': ' 0.00',
                        'house_shipment_id': '',
                        'service_job_id': '',
                        'unit': '',
                        'display_type': 'line_note',
                        'sequence': 3,
                        'tax_ids': ''
                    },
                    {
                        'product_id': '',
                        'name': 'Total',
                        'quantity': 0,
                        'currency_id': '',
                        'currency_exchange_rate': '',
                        'price_unit': '',
                        'FCY_Amt': '0.0',
                        'vat': '',
                        'Amount': ' 100.00',
                        'house_shipment_id': '',
                        'service_job_id': '',
                        'unit': '',
                        'display_type': 'line_section_total',
                        'sequence': 4,
                        'tax_ids': ''
                    },
                    {
                        'product_id': '',
                        'name': 'This is a section',
                        'quantity': 1.0,
                        'currency_id': 'INR',
                        'currency_exchange_rate': '',
                        'price_unit': '',
                        'FCY_Amt': ' 0.00',
                        'vat': ' 0.00',
                        'Amount': ' 0.00',
                        'house_shipment_id': '',
                        'service_job_id': '',
                        'unit': '',
                        'display_type': 'line_section',
                        'sequence': 5,
                        'tax_ids': ''
                    },
                    {
                        'product_id': 'Desk Stand with Screen',
                        'name': '[FURN_7888] Desk Stand with Screen-delivery',
                        'quantity': 1.0,
                        'currency_id': 'INR',
                        'currency_exchange_rate': '',
                        'price_unit': 200.0,
                        'FCY_Amt': ' 200.00',
                        'vat': ' 0.00',
                        'Amount': ' 200.00',
                        'house_shipment_id': house_shipment_1.name,
                        'service_job_id': '',
                        'unit': '',
                        'display_type': '',
                        'sequence': 6,
                        'tax_ids': ''
                    },
                    {
                        'product_id': '',
                        'name': 'Total',
                        'quantity': 0,
                        'currency_id': '',
                        'currency_exchange_rate': '',
                        'price_unit': '',
                        'FCY_Amt': '0.0',
                        'vat': '',
                        'Amount': ' 200.00',
                        'house_shipment_id': '',
                        'service_job_id': '',
                        'unit': '',
                        'display_type': 'line_section_total',
                        'sequence': 7,
                        'tax_ids': ''
                    }
                ]
            },
            {
                'id': house_shipment_2.id,
                'name': house_shipment_2.name,
                'total_amount': ' 300.00',
                'total_amount_in_words': 'Three Hundred Rupees Only',
                'total_vat': ' 0.00',
                'lines': [
                    {
                        'product_id': 'Desk Stand with Screen',
                        'name': '[FURN_7888] Desk Stand with Screen- delivery 1',
                        'quantity': 1.0,
                        'currency_id': 'INR',
                        'currency_exchange_rate': '',
                        'price_unit': 100.0,
                        'FCY_Amt': ' 100.00',
                        'vat': ' 0.00',
                        'Amount': ' 100.00',
                        'house_shipment_id': house_shipment_2.name,
                        'service_job_id': '',
                        'unit': '',
                        'display_type': '',
                        'sequence': 15,
                        'tax_ids': ''
                    },
                    {
                        'product_id': 'Desk Stand with Screen',
                        'name': '[FURN_7888] Desk Stand with Screen-delivery',
                        'quantity': 1.0,
                        'currency_id': 'INR',
                        'currency_exchange_rate': '',
                        'price_unit': 200.0,
                        'FCY_Amt': ' 200.00',
                        'vat': ' 0.00',
                        'Amount': ' 200.00',
                        'house_shipment_id': house_shipment_2.name,
                        'service_job_id': '',
                        'unit': '',
                        'display_type': '',
                        'sequence': 16,
                        'tax_ids': ''
                    },
                    {
                        'product_id': '',
                        'name': 'This is a note',
                        'quantity': 1.0,
                        'currency_id': 'INR',
                        'currency_exchange_rate': '',
                        'price_unit': '',
                        'FCY_Amt': ' 0.00',
                        'vat': ' 0.00',
                        'Amount': ' 0.00',
                        'house_shipment_id': '',
                        'service_job_id': '',
                        'unit': '',
                        'display_type': 'line_note',
                        'sequence': 17,
                        'tax_ids': ''
                    }
                ]
            }
        ]
        self.assertListEqual(lines_disc, invoice_line_disc)
        _logger.info(
            "\n\n=================== Test 09 With two House Section and Note complated sucessfully..! ===================\n")

        _logger.info(
            "\n\n=================== Started 10 test case With two House, Section, Note and Orphan charges !===================\n")
        product = self.create_product('Test Product 1')
        move_id.invoice_line_ids += self.env['account.move.line'].new({
            'currency_id': self.ref('base.INR'),
            'sequence': 6,
            'name': product.name,
            'product_id': product.id,
            'product_uom_id': product.uom_id.id,
            'quantity': 1,
            'price_unit': 100,
            'price_subtotal': 100,
            'move_id': move_id.id,
        })
        invoice_line_disc = move_id.get_invoice_line_for_document(['house_shipment_id'])
        lines_disc = [{
            'id': house_shipment_1.id,
            'name': house_shipment_1.name,
            'total_amount': ' 400.00',
            'total_amount_in_words': 'Four Hundred Rupees Only',
            'total_vat': ' 0.00',
            'lines': [
                {
                    'product_id': '',
                    'name': 'This is a section',
                    'quantity': 1.0,
                    'currency_id': 'INR',
                    'currency_exchange_rate': '',
                    'price_unit': '',
                    'FCY_Amt': ' 0.00',
                    'vat': ' 0.00',
                    'Amount': ' 0.00',
                    'house_shipment_id': '',
                    'service_job_id': '',
                    'unit': '',
                    'display_type': 'line_section',
                    'sequence': 1,
                    'tax_ids': ''
                },
                {
                    'product_id': 'Desk Stand with Screen',
                    'name': '[FURN_7888] Desk Stand with Screen- delivery 1',
                    'quantity': 1.0,
                    'currency_id': 'INR',
                    'currency_exchange_rate': '',
                    'price_unit': 100.0,
                    'FCY_Amt': ' 100.00',
                    'vat': ' 0.00',
                    'Amount': ' 100.00',
                    'house_shipment_id': house_shipment_1.name,
                    'service_job_id': '',
                    'unit': '',
                    'display_type': '',
                    'sequence': 2,
                    'tax_ids': ''
                },
                {
                    'product_id': 'Test Product 1',
                    'name': 'Test Product 1',
                    'quantity': 1.0,
                    'currency_id': 'INR',
                    'currency_exchange_rate': '',
                    'price_unit': 100.0,
                    'FCY_Amt': ' 100.00',
                    'vat': ' 0.00',
                    'Amount': ' 100.00',
                    'house_shipment_id': '',
                    'service_job_id': '',
                    'unit': '',
                    'display_type': '',
                    'sequence': 3,
                    'tax_ids': ''
                },
                {
                    'product_id': '',
                    'name': 'This is a note 2',
                    'quantity': 1.0,
                    'currency_id': 'INR',
                    'currency_exchange_rate': '',
                    'price_unit': '',
                    'FCY_Amt': ' 0.00',
                    'vat': ' 0.00',
                    'Amount': ' 0.00',
                    'house_shipment_id': '',
                    'service_job_id': '',
                    'unit': '',
                    'display_type': 'line_note',
                    'sequence': 4,
                    'tax_ids': ''
                },
                {
                    'product_id': '',
                    'name': 'Total',
                    'quantity': 0,
                    'currency_id': '',
                    'currency_exchange_rate': '',
                    'price_unit': '',
                    'FCY_Amt': '0.0',
                    'vat': '',
                    'Amount': ' 200.00',
                    'house_shipment_id': '',
                    'service_job_id': '',
                    'unit': '',
                    'display_type': 'line_section_total',
                    'sequence': 5,
                    'tax_ids': ''
                },
                {
                    'product_id': '',
                    'name': 'This is a section',
                    'quantity': 1.0,
                    'currency_id': 'INR',
                    'currency_exchange_rate': '',
                    'price_unit': '',
                    'FCY_Amt': ' 0.00',
                    'vat': ' 0.00',
                    'Amount': ' 0.00',
                    'house_shipment_id': '',
                    'service_job_id': '',
                    'unit': '',
                    'display_type': 'line_section',
                    'sequence': 6,
                    'tax_ids': ''
                },
                {
                    'product_id': 'Desk Stand with Screen',
                    'name': '[FURN_7888] Desk Stand with Screen-delivery',
                    'quantity': 1.0,
                    'currency_id': 'INR',
                    'currency_exchange_rate': '',
                    'price_unit': 200.0,
                    'FCY_Amt': ' 200.00',
                    'vat': ' 0.00',
                    'Amount': ' 200.00',
                    'house_shipment_id': house_shipment_1.name,
                    'service_job_id': '',
                    'unit': '',
                    'display_type': '',
                    'sequence': 7,
                    'tax_ids': ''
                },
                {
                    'product_id': '',
                    'name': 'Total',
                    'quantity': 0,
                    'currency_id': '',
                    'currency_exchange_rate': '',
                    'price_unit': '',
                    'FCY_Amt': '0.0',
                    'vat': '',
                    'Amount': ' 200.00',
                    'house_shipment_id': '',
                    'service_job_id': '',
                    'unit': '',
                    'display_type': 'line_section_total',
                    'sequence': 8,
                    'tax_ids': ''
                }
            ]
        },
            {
                'id': house_shipment_2.id,
                'name': house_shipment_2.name,
                'total_amount': ' 300.00',
                'total_amount_in_words': 'Three Hundred Rupees Only',
                'total_vat': ' 0.00',
                'lines': [
                    {
                        'product_id': 'Desk Stand with Screen',
                        'name': '[FURN_7888] Desk Stand with Screen- delivery 1',
                        'quantity': 1.0,
                        'currency_id': 'INR',
                        'currency_exchange_rate': '',
                        'price_unit': 100.0,
                        'FCY_Amt': ' 100.00',
                        'vat': ' 0.00',
                        'Amount': ' 100.00',
                        'house_shipment_id': house_shipment_2.name,
                        'service_job_id': '',
                        'unit': '',
                        'display_type': '',
                        'sequence': 15,
                        'tax_ids': ''
                    },
                    {
                        'product_id': 'Desk Stand with Screen',
                        'name': '[FURN_7888] Desk Stand with Screen-delivery',
                        'quantity': 1.0,
                        'currency_id': 'INR',
                        'currency_exchange_rate': '',
                        'price_unit': 200.0,
                        'FCY_Amt': ' 200.00',
                        'vat': ' 0.00',
                        'Amount': ' 200.00',
                        'house_shipment_id': house_shipment_2.name,
                        'service_job_id': '',
                        'unit': '',
                        'display_type': '',
                        'sequence': 16,
                        'tax_ids': ''
                    },
                    {
                        'product_id': '',
                        'name': 'This is a note',
                        'quantity': 1.0,
                        'currency_id': 'INR',
                        'currency_exchange_rate': '',
                        'price_unit': '',
                        'FCY_Amt': ' 0.00',
                        'vat': ' 0.00',
                        'Amount': ' 0.00',
                        'house_shipment_id': '',
                        'service_job_id': '',
                        'unit': '',
                        'display_type': 'line_note',
                        'sequence': 17,
                        'tax_ids': ''
                    }
                ]}]
        self.assertListEqual(lines_disc, invoice_line_disc)
        _logger.info(
            "\n\n=================== Test 10 With two House, Section, Note and Orphan charges complated sucessfully..! ===================\n")