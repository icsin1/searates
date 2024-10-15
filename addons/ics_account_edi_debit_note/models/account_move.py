from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_document_type(self):
        self.ensure_one()
        return 'debit_note' if self.debit_origin_id else super()._get_document_type()
