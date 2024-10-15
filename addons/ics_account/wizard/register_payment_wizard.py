from odoo import models, api, _
from odoo.exceptions import ValidationError
from datetime import date


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    @api.constrains('amount')
    def _check_amount(self):
        if not self._context.get('click_from_treeview') and not self._context.get('click_from_treeview') == True:
            for record in self:
                # Restrict user to Register Payment with Zero About, But Allow Zero amount to Post Difference to Selected Writeoff-account
                if record.amount <= 0 and (record.payment_difference_handling != 'reconcile' or not record.writeoff_account_id):
                    raise ValidationError(_('You can only register a payment with an amount greater than zero.'))

    @api.constrains('payment_date')
    def _check_payment_date(self):
        for record in self:
            if record.payment_date > date.today():
                raise ValidationError(_('Future dates are not allowed, Register payment with past/today\'s date.'))
