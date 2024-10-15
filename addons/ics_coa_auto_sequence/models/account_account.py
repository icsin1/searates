
from odoo import models, api


class AccountAccount(models.Model):
    _inherit = 'account.account'

    @api.onchange('user_type_id')
    def _onchange_user_type_id(self):
        super(AccountAccount, self)._onchange_user_type_id()
        if not self.user_type_id or self._origin or self._origin.user_type_id.id == self.user_type_id.id:
            return

        account_type_sequence_id = self.get_account_type_sequence()
        if account_type_sequence_id:
            self.code = '{}{}'.format(account_type_sequence_id.code, account_type_sequence_id.next_no)

    @api.model
    def create(self, vals):
        res = super(AccountAccount, self).create(vals)
        for rec in res:
            account_type_sequence_id = rec.get_account_type_sequence()
            if account_type_sequence_id:
                account_type_sequence_id.next_no += 1
        return res

    def get_account_type_sequence(self):
        account_type_sequence_id = self.env['account.type.sequence'].search(
            [('account_type_id', '=', self.user_type_id.id), ('company_id', '=', self.company_id.id)], limit=1)
        return account_type_sequence_id
