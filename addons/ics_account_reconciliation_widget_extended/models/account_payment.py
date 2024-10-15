# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def validate_reconciliation(self):
        for payment in self:
            is_reconciled_with_bank = False
            statement_line_id = payment.move_id.line_ids.filtered(lambda line: line.statement_id)
            if statement_line_id:
                is_reconciled_with_bank = True
            elif payment.pdc_payment_id and payment.pdc_payment_id.is_reconciled:
                is_reconciled_with_bank = True
            if is_reconciled_with_bank:
                raise ValidationError(_("This payment is reconciled with the bank statement; please revert the bank statement reconciliation before cancelling this payment."))

    def action_draft(self):
        self.validate_reconciliation()
        return super().action_draft()

    def unlink(self):
        self.validate_reconciliation()
        return super().unlink()
