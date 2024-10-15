import time

from odoo.tests import tagged
from odoo.addons.ics_account.tests.common import PaymentAdjustmentCommon


@tagged('post_install', '-at_install')
class TestAccountPaymentAdjustment(PaymentAdjustmentCommon):

    def setUp(self):
        super().setUp()
        self.company = self.company_data.get('company')

    def test_invoice_full_payment_adjustment(self):
        """ Local Currency: AED
            Invoice Currency: AED

            Payment currency: AED
            Adjusting full payment
        """
        invoice_data = {
            'invoice_amount': 368.5,
            'invoice_currency': self.currency_aed,
        }
        payment_data = {
            'payment_amount': 368.5,
            'payment_currency': self.currency_aed
        }
        result_data = {
            'invoice_payment_status': 'in_payment',
            'adjustment_amount': 368.5
        }
        self._validate_payment_adjustment(invoice_data, payment_data, result_data, move_type='in_invoice')

    def test_invoice_partial_less_payment_adjustment(self):
        """ Local Currency: AED
            Invoice Currency: AED

            Payment currency: AED
            Adjusting partial less payment amount
        """
        invoice_data = {
            'invoice_amount': 368.5,
            'invoice_currency': self.currency_aed,
        }
        payment_data = {
            'payment_amount': 150,
            'payment_currency': self.currency_aed
        }
        result_data = {
            'invoice_payment_status': 'partial',
            'adjustment_amount': 150
        }
        self._validate_payment_adjustment(invoice_data, payment_data, result_data, move_type='in_invoice')

    def test_invoice_full_more_payment_adjustment(self):
        """ Local Currency: AED
            Invoice Currency: AED

            Payment currency: AED
            Adjusting full with more payment amount
        """
        invoice_data = {
            'invoice_amount': 368.5,
            'invoice_currency': self.currency_aed,
        }
        payment_data = {
            'payment_amount': 400,
            'payment_currency': self.currency_aed
        }
        result_data = {
            'invoice_payment_status': 'in_payment',
            'adjustment_amount': 368.5
        }
        self._validate_payment_adjustment(invoice_data, payment_data, result_data, move_type='in_invoice')

    def test_invoice_partial_more_payment_adjustment(self):
        """ Local Currency: AED
            Invoice Currency: AED

            Payment currency: AED
            Adjusting partial with more payment amount
        """
        invoice_data = {
            'invoice_amount': 368.5,
            'invoice_currency': self.currency_aed,
        }
        payment_data = {
            'payment_amount': 400,
            'payment_currency': self.currency_aed
        }
        result_data = {
            'invoice_payment_status': 'partial',
            'adjustment_amount': 150
        }
        self._validate_payment_adjustment(invoice_data, payment_data, result_data, move_type='in_invoice')

    def test_invoice_full_foreign_payment_adjustment(self):
        """ Local Currency: AED
            Invoice Currency: AED

            Payment currency: USD
            Adjusting partial with more payment amount
        """
        invoice_data = {
            'invoice_amount': 368.5,
            'invoice_currency': self.currency_aed,
        }
        payment_data = {
            'payment_amount': 100,
            'payment_currency': self.currency_usd
        }
        result_data = {
            'invoice_payment_status': 'in_payment',
            'adjustment_amount': 368.5
        }
        self._validate_payment_adjustment(invoice_data, payment_data, result_data, move_type='in_invoice')

    def test_invoice_foreign_less_payment_adjustment(self):
        """ Local Currency: AED
            Invoice Currency: AED

            Payment currency: USD
            Adjusting partial with less payment amount
        """
        invoice_data = {
            'invoice_amount': 368.5,
            'invoice_currency': self.currency_aed,
        }
        payment_data = {
            'payment_amount': 50,
            'payment_currency': self.currency_usd
        }
        result_data = {
            'invoice_payment_status': 'partial',
            'adjustment_amount': 184.25
        }
        self._validate_payment_adjustment(invoice_data, payment_data, result_data, move_type='in_invoice')

    def test_invoice_foreign_more_payment_adjustment(self):
        """ Local Currency: AED
            Invoice Currency: AED

            Payment currency: USD
            Adjusting partial with more payment amount
        """
        invoice_data = {
            'invoice_amount': 368.5,
            'invoice_currency': self.currency_aed,
        }
        payment_data = {
            'payment_amount': 150,
            'payment_currency': self.currency_usd
        }
        result_data = {
            'invoice_payment_status': 'in_payment',
            'adjustment_amount': 368.5
        }
        self._validate_payment_adjustment(invoice_data, payment_data, result_data, move_type='in_invoice')

    def test_invoice_foreign_partial_more_payment_adjustment(self):
        """ Local Currency: AED
            Invoice Currency: AED

            Payment currency: USD
            Adjusting partial with more payment amount
        """
        invoice_data = {
            'invoice_amount': 368.5,
            'invoice_currency': self.currency_aed,
        }
        payment_data = {
            'payment_amount': 150,
            'payment_currency': self.currency_usd
        }
        result_data = {
            'invoice_payment_status': 'partial',
            'adjustment_amount': 150.0
        }
        self._validate_payment_adjustment(invoice_data, payment_data, result_data, move_type='in_invoice')
