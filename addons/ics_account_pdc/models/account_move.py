# -*- coding: utf-8 -*-

from odoo import api, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.pdc_payment_id.state',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.pdc_payment_id.state',
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.pdc_payment_id.is_reconciled',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.pdc_payment_id.is_reconciled',
    )
    def _compute_amount(self):
        res = super()._compute_amount()
        for move in self:
            reconciled_payments = move._get_reconciled_payments().filtered(lambda payment: payment.payment_method_id.code == 'pdc')
            not_reconciled_pdc_payments = reconciled_payments.filtered(lambda payment: payment.pdc_payment_id and not payment.pdc_payment_id.is_reconciled)
            if move.payment_state == "paid" and not_reconciled_pdc_payments:
                move.payment_state = move._get_invoice_in_payment_state()
        return res
