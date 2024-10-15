from odoo import models, fields


class JournalMoveSequence(models.Model):
    _name = 'journal.move.sequence'
    _description = 'Journal Move Sequence'
    _order = 'sequence'

    journal_id = fields.Many2one('account.journal', ondelete='cascade')
    freight_product_id = fields.Many2one('freight.product', 'Main Freight Product')
    sequence_id = fields.Many2one('ir.sequence', 'Main Sequence')
    reverse_sequence_id = fields.Many2one('ir.sequence', 'Reverse Sequence')
    sequence = fields.Integer(default=0)
