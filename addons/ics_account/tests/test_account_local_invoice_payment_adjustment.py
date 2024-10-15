import time

from odoo.tests import tagged
from odoo.addons.ics_account.tests.common import PaymentAdjustmentCommon


@tagged('post_install', '-at_install')
class TestAccountPaymentAdjustment(PaymentAdjustmentCommon):

    def setUp(self):
        super().setUp()
        self.company = self.company_data.get('company')

    def test_local_currency_payment(self):
        """ Local Currency: AED
            Invoice Currency: AED

            Payment currency: AED
            Validation payment and remaining amount
        """
        # Creating new payment in AED for Amount 100 AED
        payment = self.env['account.payment'].create({
            'amount': 100.0,
            'date': time.strftime('%Y') + '-07-02',
            'currency_id': self.currency_aed.get('currency').id,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': self.partner_a.id
        })
        payment.action_post()
        self.assertEqual(payment.currency_id, self.currency_aed.get('currency'), 'Payment currency must be in AED')
        for payment_line in payment.line_ids:
            if payment_line.debit:
                self.assertEqual(payment_line.debit, 100.0, 'Payment Line Debit amount in local currency must match')
            if payment_line.credit:
                self.assertEqual(payment_line.credit, 100.0, 'Payment Line Credit amount in local currency must match')

        self.assertEqual(payment.total_remaining_amount, 100.0, 'Total Remaining amount should be 100.0 AED')

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
        self._validate_payment_adjustment(invoice_data, payment_data, result_data)

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
        self._validate_payment_adjustment(invoice_data, payment_data, result_data)

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
        self._validate_payment_adjustment(invoice_data, payment_data, result_data)

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
        self._validate_payment_adjustment(invoice_data, payment_data, result_data)

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
        self._validate_payment_adjustment(invoice_data, payment_data, result_data)

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
        self._validate_payment_adjustment(invoice_data, payment_data, result_data)

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
        self._validate_payment_adjustment(invoice_data, payment_data, result_data)

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
        self._validate_payment_adjustment(invoice_data, payment_data, result_data)
