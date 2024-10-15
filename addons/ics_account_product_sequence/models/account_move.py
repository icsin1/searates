from odoo import models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends("state", "journal_id", "date")
    def _compute_name_by_sequence(self):
        dynamic_seq_move_ids = self.filtered(
            lambda m: m.journal_id.seq_base_on_product and m.state == 'posted' and (not m.name or m.name == "/")
        )
        if dynamic_seq_move_ids:
            for move in dynamic_seq_move_ids:
                move_sequence = move.journal_id._find_move_sequence(move)
                move.name = move_sequence.with_context(ir_sequence_date=move.date).next_by_id()
        return super(AccountMove, self - dynamic_seq_move_ids)._compute_name_by_sequence()
