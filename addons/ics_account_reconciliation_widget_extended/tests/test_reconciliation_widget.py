import logging
import time

import odoo.tests
from odoo.tools.misc import NON_BREAKING_SPACE

from odoo.addons.account.tests.common import TestAccountReconciliationCommon

_logger = logging.getLogger(__name__)


@odoo.tests.tagged("post_install", "-at_install")
class TestReconciliationWidget(TestAccountReconciliationCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.acc_bank_stmt_model = cls.env["account.bank.statement"]
        cls.acc_bank_stmt_line_model = cls.env["account.bank.statement.line"]

    def test_unreconcile(self):
        # Use case:
        # 2 invoices paid with a single payment. Unreconcile the payment with one invoice, the
        # other invoice should remain reconciled.
        inv1 = self.create_invoice(invoice_amount=10, currency_id=self.currency_usd_id)
        inv2 = self.create_invoice(invoice_amount=20, currency_id=self.currency_usd_id)
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'payment_method_line_id': self.inbound_payment_method_line.id,
            'partner_type': 'customer',
            'partner_id': self.partner_agrolait_id,
            'amount': 100,
            'currency_id': self.currency_usd_id,
            'journal_id': self.bank_journal_usd.id,
        })
        payment.action_post()
        credit_aml = payment.line_ids.filtered('credit')

        # Check residual before assignation
        self.assertAlmostEqual(inv1.amount_residual, 10)
        self.assertAlmostEqual(inv2.amount_residual, 20)

        # Assign credit and residual
        inv1.js_assign_outstanding_line(credit_aml.id)
        inv2.js_assign_outstanding_line(credit_aml.id)
        self.assertAlmostEqual(inv1.amount_residual, 0)
        self.assertAlmostEqual(inv2.amount_residual, 0)

        # Unreconcile one invoice at a time and check residual
        credit_aml.remove_move_reconcile()
        self.assertAlmostEqual(inv1.amount_residual, 10)
        self.assertAlmostEqual(inv2.amount_residual, 20)

    def test_bank_statment_payment(self):
        # Use case:
        # 2 invoices paid with a single payment. Unreconcile the payment with one invoice, the
        # other invoice should remain reconciled.
        partner1 = self.env["res.partner"].create(
            {
                "name": "test",
            }
        )
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'payment_method_line_id': self.inbound_payment_method_line.id,
            'partner_type': 'customer',
            'partner_id': partner1,
            'amount': 100,
            'currency_id': self.currency_usd_id,
            'journal_id': self.bank_journal_usd.id,
            "date": time.strftime("%Y-07-14"),

        })
        payment.action_post()

        bank_stmt = self.acc_bank_stmt_model.create(
            {
                "journal_id": self.bank_journal_usd.id,
                "date": time.strftime("%Y-07-15"),
                "name": "payment %s" % payment.name,
            }
        )

        bank_stmt_line = self.acc_bank_stmt_line_model.create(
            {
                "payment_ref": "payment",
                "statement_id": bank_stmt.id,
                "partner_id": self.partner_agrolait_id,
                "amount": 50,
                "date": time.strftime("%Y-07-15"),
            }
        )

        # Check residual before assignation
        result1 = self.env["account.reconciliation.widget"].get_bank_statement_line_data(
            bank_stmt_line.ids
        )

        self.assertEqual(
            result1["lines"][0]["reconciliation_proposition"][0]["amount_str"],
            f"${NON_BREAKING_SPACE}50.00",
        )
        self.assertEqual(
            result1["lines"][0]["reconciliation_proposition"][0]["amount_str"],
            f"${NON_BREAKING_SPACE}50.00",
        )
