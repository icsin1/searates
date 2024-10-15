import ast
from odoo import models, fields, _
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    seq_base_on_product = fields.Boolean('Sequence Base On Product')
    journal_move_sequence_ids = fields.One2many('journal.move.sequence', 'journal_id')

    def _match_move_sequence(self, move):
        self.ensure_one()
        for move_sequence in self.journal_move_sequence_ids:
            data_domain = ast.literal_eval(move_sequence.freight_product_id.match_domain or '[]')
            matched = move.search(data_domain + [('id', 'in', move.ids)])
            if matched:
                return move_sequence
        return False

    def _find_move_sequence(self, move):
        self.ensure_one()
        move_sequence = self._match_move_sequence(move)
        if not move_sequence:
            raise ValidationError(_('Unable to find Move Sequence Based on defined Rules. Provide matching rule in Journal'))

        if move.move_type in ("out_refund", "in_refund") and move.journal_id.type in ("sale", "purchase"):
            sequence_id = move_sequence.reverse_sequence_id
        else:
            sequence_id = move_sequence.sequence_id
        return sequence_id
