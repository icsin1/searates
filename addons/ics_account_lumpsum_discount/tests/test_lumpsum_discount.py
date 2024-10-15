# -*- coding: utf-8 -*-
from odoo.tests import common


class TestInvoiceLumpsumDiscount(common.TransactionCase):

    def setUp(self):
        super(TestInvoiceLumpsumDiscount, self).setUp()

        self.partner = self.env['res.partner'].search([], limit=1)
        self.product = self.env['product.product'].search([], limit=1)
        self.account = self.env['account.account'].search([('code', '=', '200110')], limit=1)

    def test_invoice_lumpsum_discount(self):
        invoice = self.env['account.move'].create({
            'invoice_date': '2024-05-29',
            'partner_id': self.partner.id,
            'move_type': 'out_invoice',
        })
        invoice.invoice_line_ids = [(0, 0, {
            'product_id': self.product.id,
            'name': 'Test Product 1',
            'account_id': self.account.id,
            'quantity': 2,
            'price_unit': 100.0,
            'lumpsum_discount': 20.0,
            'price_subtotal': 180.0,
        })]
        self.discount = (invoice.invoice_line_ids.lumpsum_discount * 100) / (invoice.invoice_line_ids.price_unit * invoice.invoice_line_ids.quantity)
        self.assertEqual(self.discount, 10.0, 'Value not match.')

        invoice.invoice_line_ids = [(0, 0, {
            'product_id': self.product.id,
            'name': 'Test Product 1',
            'account_id': self.account.id,
            'quantity': 2,
            'price_unit': 100.0,
            'discount': 10.0,
            'price_subtotal': 180.0,
        })]
        self.lumpsum_discount = (invoice.invoice_line_ids[1].price_unit * invoice.invoice_line_ids[1].quantity) * (invoice.invoice_line_ids[1].discount / 100)
        self.assertEqual(self.lumpsum_discount, 20.0, 'Value not match.')

    def test_vendor_bill_lumpsum_discount(self):
        invoice = self.env['account.move'].create({
            'invoice_date': '2024-05-30',
            'partner_id': self.partner.id,
            'move_type': 'in_invoice',
        })
        invoice.invoice_line_ids = [(0, 0, {
            'product_id': self.product.id,
            'name': 'Test Product 2',
            'account_id': self.account.id,
            'quantity': 1,
            'price_unit': 100.0,
            'lumpsum_discount': 10.0,
            'price_subtotal': 90.0,
        })]
        self.discount = (invoice.invoice_line_ids.lumpsum_discount * 100) / (invoice.invoice_line_ids.price_unit * invoice.invoice_line_ids.quantity)
        self.assertEqual(self.discount, 10.0, 'Value not match.')

        invoice.invoice_line_ids = [(0, 0, {
            'product_id': self.product.id,
            'name': 'Test Product 2',
            'account_id': self.account.id,
            'quantity': 1,
            'price_unit': 100.0,
            'discount': 10.0,
            'price_subtotal': 90.0,
        })]
        self.lumpsum_discount = (invoice.invoice_line_ids[1].price_unit * invoice.invoice_line_ids[1].quantity) * (invoice.invoice_line_ids[1].discount / 100)
        self.assertEqual(self.lumpsum_discount, 10.0, 'Value not match.')
