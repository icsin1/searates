from odoo import models, fields, _
from odoo.exceptions import ValidationError


class AccountingLockDates(models.TransientModel):
    _name = 'accounting.lock.dates'
    _description = 'Lock Dates'

    journal_entry_lock_date = fields.Date(default=lambda self: self.env.company.fiscalyear_lock_date)

    def action_save_lock_date(self):
        self.ensure_one()
        if self.user_has_groups('account.group_account_manager'):
            if self.journal_entry_lock_date and self.journal_entry_lock_date > fields.Date.context_today(self):
                raise ValidationError(_("You cannot set lock date in the future."))
            self.env.company.sudo().write({
                'fiscalyear_lock_date': self.journal_entry_lock_date,
            })
        else:
            raise ValidationError(_("Only Billing Administrators are allowed to changes the date"))
        return {'type': 'ir.actions.act_window_close'}
