from odoo.tests import tagged
from odoo.addons.ics_account.tests.common import PaymentAdjustmentCommon


@tagged('post_install', '-at_install')
class TestAccountMultiInvoicePaymentAdjustment(PaymentAdjustmentCommon):

    def setUp(self):
        super().setUp()
        self.company = self.company_data.get('company')

    def test_multi_bill_foreign_currency_partial_payment_adjustment(self):
        invoices = [
            {
                'invoice_amount': 100,
                'invoice_currency': self.currency_usd,
                'invoice_payment_status': 'partial',
                'adjustment_amount': 184.25
            },
            {
                'invoice_amount': 200,
                'invoice_currency': self.currency_usd,
                'invoice_payment_status': 'partial',
                'adjustment_amount': 368.5
            }
        ]
        payment_data = {
            'payment_amount': 400,
            'payment_currency': self.currency_usd
        }
        self._validate_multi_invoice_payment_adjustment(invoices, payment_data, move_type='in_invoice')

    def test_multi_bill_foreign_currency_local_payment_adjustment(self):
        invoices = [
            {
                'invoice_amount': 100,
                'invoice_currency': self.currency_usd,
                'invoice_payment_status': 'partial',
                'adjustment_amount': 184.25
            },
            {
                'invoice_amount': 200,
                'invoice_currency': self.currency_usd,
                'invoice_payment_status': 'partial',
                'adjustment_amount': 368.5
            }
        ]
        payment_data = {
            'payment_amount': 1200,
            'payment_currency': self.currency_aed
        }
        self._validate_multi_invoice_payment_adjustment(invoices, payment_data, move_type='in_invoice')

    def test_multi_bill_local_currency_foreign_payment_adjustment(self):
        invoices = [
            {
                'invoice_amount': 368.5,
                'invoice_currency': self.currency_aed,
                'invoice_payment_status': 'partial',
                'adjustment_amount': 184.25
            },
            {
                'invoice_amount': 737,
                'invoice_currency': self.currency_aed,
                'invoice_payment_status': 'partial',
                'adjustment_amount': 368.5
            }
        ]
        payment_data = {
            'payment_amount': 400,
            'payment_currency': self.currency_usd
        }
        self._validate_multi_invoice_payment_adjustment(invoices, payment_data, move_type='in_invoice')

    def test_multi_bill_local_currency_local_payment_adjustment(self):
        invoices = [
            {
                'invoice_amount': 368.5,
                'invoice_currency': self.currency_aed,
                'invoice_payment_status': 'partial',
                'adjustment_amount': 184.25
            },
            {
                'invoice_amount': 737,
                'invoice_currency': self.currency_aed,
                'invoice_payment_status': 'partial',
                'adjustment_amount': 368.5
            }
        ]
        payment_data = {
            'payment_amount': 1200,
            'payment_currency': self.currency_aed
        }
        self._validate_multi_invoice_payment_adjustment(invoices, payment_data, move_type='in_invoice')

    def test_multi_bill_currency_foreign_payment_adjustment(self):
        invoices = [
            {
                'invoice_amount': 368.5,
                'invoice_currency': self.currency_aed,
                'invoice_payment_status': 'partial',
                'adjustment_amount': 184.25
            },
            {
                'invoice_amount': 100,
                'invoice_currency': self.currency_usd,
                'invoice_payment_status': 'partial',
                'adjustment_amount': 184.25
            }
        ]
        payment_data = {
            'payment_amount': 250,
            'payment_currency': self.currency_usd
        }
        self._validate_multi_invoice_payment_adjustment(invoices, payment_data, move_type='in_invoice')

    def test_multi_bill_currency_local_payment_adjustment(self):
        invoices = [
            {
                'invoice_amount': 368.5,
                'invoice_currency': self.currency_aed,
                'invoice_payment_status': 'partial',
                'adjustment_amount': 184.25
            },
            {
                'invoice_amount': 100,
                'invoice_currency': self.currency_usd,
                'invoice_payment_status': 'partial',
                'adjustment_amount': 184.25
            }
        ]
        payment_data = {
            'payment_amount': 800,
            'payment_currency': self.currency_aed
        }
        self._validate_multi_invoice_payment_adjustment(invoices, payment_data, move_type='in_invoice')

    def test_multi_bill_foreign_currency_foreign_payment_adjustment(self):
        invoices = [
            {
                'invoice_amount': 27.14,
                'invoice_currency': self.currency_usd,
                'invoice_payment_status': 'partial',
                'adjustment_amount': 50
            },
            {
                'invoice_amount': 25.13,
                'invoice_currency': self.currency_eur,
                'invoice_payment_status': 'partial',
                'adjustment_amount': 50
            }
        ]
        payment_data = {
            'payment_amount': 60,
            'payment_currency': self.currency_usd
        }
        self._validate_multi_invoice_payment_adjustment(invoices, payment_data, move_type='in_invoice')

    def test_multi_bill_foreign_currencies_local_payment_adjustment(self):
        invoices = [
            {
                'invoice_amount': 27.14,
                'invoice_currency': self.currency_usd,
                'invoice_payment_status': 'partial',
                'adjustment_amount': 50
            },
            {
                'invoice_amount': 25.13,
                'invoice_currency': self.currency_eur,
                'invoice_payment_status': 'partial',
                'adjustment_amount': 50
            }
        ]
        payment_data = {
            'payment_amount': 250,
            'payment_currency': self.currency_aed
        }
        self._validate_multi_invoice_payment_adjustment(invoices, payment_data, move_type='in_invoice')

    def test_multi_bill_foreign_currencies_foreign_payment_adjustment(self):
        invoices = [
            {
                'invoice_amount': 27.14,
                'invoice_currency': self.currency_usd,
                'invoice_payment_status': 'partial',
                'adjustment_amount': 50
            },
            {
                'invoice_amount': 25.13,
                'invoice_currency': self.currency_eur,
                'invoice_payment_status': 'partial',
                'adjustment_amount': 50
            }
        ]
        payment_data = {
            'payment_amount': 5000,
            'payment_currency': self.currency_inr
        }
        self._validate_multi_invoice_payment_adjustment(invoices, payment_data, move_type='in_invoice')

    def test_multi_bill_currencies_foreign_payment_adjustment(self):
        invoices = [
            {
                'invoice_amount': 27.14,
                'invoice_currency': self.currency_usd,
                'invoice_payment_status': 'partial',
                'adjustment_amount': 50
            },
            {
                'invoice_amount': 100,
                'invoice_currency': self.currency_aed,
                'invoice_payment_status': 'partial',
                'adjustment_amount': 50
            }
        ]
        payment_data = {
            'payment_amount': 5000,
            'payment_currency': self.currency_inr
        }
        self._validate_multi_invoice_payment_adjustment(invoices, payment_data, move_type='in_invoice')
