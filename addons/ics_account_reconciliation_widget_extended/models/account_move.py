from odoo import api, models, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    def js_remove_outstanding_partial(self, partial_id):
        ''' Called by the 'payment' widget to remove a reconciled entry to the present invoice.

        :param partial_id: The id of an existing partial reconciled with the current invoice.
        '''
        self.ensure_one()
        if self.payment_id and self.payment_id.reconciled_statement_ids:
            raise ValidationError(_('Please Un Reconcile Bank Statement.'))
        partial = self.env['account.partial.reconcile'].browse(partial_id)
        return partial.unlink()
