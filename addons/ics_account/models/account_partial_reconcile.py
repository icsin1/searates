from odoo import models, _


class AccountPartialReconcile(models.Model):
    _inherit = 'account.partial.reconcile'

    def unlink(self):
        for rec in self:
            rec.debit_move_id.move_id.message_post(body=_('Amount {} unlinked from move {}'.format(rec.amount, rec.credit_move_id.move_id.display_name)))
            rec.credit_move_id.move_id.message_post(body=_('Amount {} unlinked from move {}'.format(rec.amount, rec.debit_move_id.move_id.display_name)))
        return super().unlink()
