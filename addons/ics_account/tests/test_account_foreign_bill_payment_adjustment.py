from odoo.tests import tagged
from odoo.addons.ics_account.tests.common import PaymentAdjustmentCommon


@tagged('post_install', '-at_install')
class TestAccountBillPaymentAdjustment(PaymentAdjustmentCommon):

    def setUp(self):
        super().setUp()
        self.company = self.company_data.get('company')

    def test_bill_foreign_currency_full_payment_adjustment(self):
        invoice_data = {
            'invoice_amount': 100,
            'invoice_currency': self.currency_usd,
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

    def test_bill_foreign_currency_partial_amount_adjustment(self):
        """ Local Currency: AED
            Invoice Currency: USD

            Payment currency: USD
            Adjustment partial amount as invoice amount
        """
        invoice_data = {
            'invoice_amount': 100,
            'invoice_currency': self.currency_usd,
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

    def test_bill_foreign_currency_partial_amount_with_more_payment(self):
        invoice_data = {
            'invoice_amount': 100,
            'invoice_currency': self.currency_usd,
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

    def test_bill_foreign_currency_partial_amount_with_partial_adjust(self):
        """ Local Currency: AED
            Invoice Currency: USD

            Payment currency: USD
            Partial payment with partial adjustment on payment
        """
        invoice_data = {
            'invoice_amount': 100,
            'invoice_currency': self.currency_usd,
        }
        payment_data = {
            'payment_amount': 150,
            'payment_currency': self.currency_usd
        }
        result_data = {
            'invoice_payment_status': 'partial',
            'adjustment_amount': 184.25
        }
        self._validate_payment_adjustment(invoice_data, payment_data, result_data, move_type='in_invoice')

    def test_bill_foreign_currency_local_currency_adjust(self):
        """ Local Currency: AED
            Invoice Currency: USD

            Payment currency: AED
            Invoice with USD adjusting payment AED
        """
        invoice_data = {
            'invoice_amount': 100,
            'invoice_currency': self.currency_usd,
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

    def test_bill_foreign_invoice_local_currency_adjustment(self):
        """ Local Currency: AED
            Invoice Currency: USD

            Payment currency: AED
            Adjusting USD Invoice with partial AED Amount
        """
        invoice_data = {
            'invoice_amount': 100,
            'invoice_currency': self.currency_usd,
        }
        payment_data = {
            'payment_amount': 368.5,
            'payment_currency': self.currency_aed
        }
        result_data = {
            'invoice_payment_status': 'partial',
            'adjustment_amount': 150.0
        }
        self._validate_payment_adjustment(invoice_data, payment_data, result_data, move_type='in_invoice')

    def test_bill_foreign_invoice_local_more_payment_currency_adjustment(self):
        """ Local Currency: AED
            Invoice Currency: USD

            Payment currency: AED
            Adjusting invoice with payment more than invoice amount
        """
        invoice_data = {
            'invoice_amount': 100,
            'invoice_currency': self.currency_usd,
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

    def test_bill_foreign_invoice_local_more_payment_currency_partial_adjustment(self):
        """ Local Currency: AED
            Invoice Currency: USD

            Payment currency: AED
            Adjusting invoice with payment more than invoice amount and partial adjustment
        """
        invoice_data = {
            'invoice_amount': 100,
            'invoice_currency': self.currency_usd,
        }
        payment_data = {
            'payment_amount': 400,
            'payment_currency': self.currency_aed
        }
        result_data = {
            'invoice_payment_status': 'partial',
            'adjustment_amount': 150.0
        }
        self._validate_payment_adjustment(invoice_data, payment_data, result_data, move_type='in_invoice')

    def test_bill_foreign_invoice_local_equal_payment_currency_partial_adjustment(self):
        """ Local Currency: AED
            Invoice Currency: USD

            Payment currency: AED
            Adjusting invoice with payment more than invoice amount and partial adjustment
        """
        invoice_data = {
            'invoice_amount': 100,
            'invoice_currency': self.currency_usd,
        }
        payment_data = {
            'payment_amount': 100,
            'payment_currency': self.currency_aed,
            'payment_adjust_amount': 50
        }
        result_data = {
            'invoice_payment_status': 'partial',
            'adjustment_amount': 50
        }
        self._validate_payment_adjustment(invoice_data, payment_data, result_data, move_type='in_invoice')
