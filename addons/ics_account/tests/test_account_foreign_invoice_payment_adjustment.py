from odoo.tests import tagged
from odoo.addons.ics_account.tests.common import PaymentAdjustmentCommon


@tagged('post_install', '-at_install')
class TestAccountPaymentAdjustment(PaymentAdjustmentCommon):

    def setUp(self):
        super().setUp()
        self.company = self.company_data.get('company')

    def test_foreign_currency_payment(self):
        """ Local Currency: AED
            Invoice Currency: USD

            Payment currency: USD
            Validation payment and remaining amount
        """
        # Creating new payment in USD for Amount 100 USD
        payment = self.create_payment(100.0, self.currency_usd.get('currency'), auto_post=True)
        self.assertEqual(payment.currency_id, self.currency_usd.get('currency'), 'Payment currency must be in USD')
        for payment_line in payment.line_ids:
            if payment_line.debit:
                self.assertEqual(payment_line.debit, 368.5, 'Payment Line Debit amount in local currency must match')
            if payment_line.credit:
                self.assertEqual(payment_line.credit, 368.5, 'Payment Line Credit amount in local currency must match')

        self.assertEqual(payment.total_remaining_amount, 368.5, 'Total Remaining amount should be 368.5 AED')

    def test_foreign_currency_full_payment_adjustment(self):
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
        self._validate_payment_adjustment(invoice_data, payment_data, result_data)

    def test_foreign_currency_partial_amount_adjustment(self):
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
        self._validate_payment_adjustment(invoice_data, payment_data, result_data)

    def test_foreign_currency_partial_amount_with_more_payment(self):
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
        self._validate_payment_adjustment(invoice_data, payment_data, result_data)

    def test_foreign_currency_partial_amount_with_partial_adjust(self):
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
        self._validate_payment_adjustment(invoice_data, payment_data, result_data)

    def test_foreign_currency_local_currency_adjust(self):
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
        self._validate_payment_adjustment(invoice_data, payment_data, result_data)

    def test_foreign_invoice_local_currency_adjustment(self):
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
        self._validate_payment_adjustment(invoice_data, payment_data, result_data)

    def test_foreign_invoice_local_more_payment_currency_adjustment(self):
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
        self._validate_payment_adjustment(invoice_data, payment_data, result_data)

    def test_foreign_invoice_local_more_payment_currency_partial_adjustment(self):
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
        self._validate_payment_adjustment(invoice_data, payment_data, result_data)
