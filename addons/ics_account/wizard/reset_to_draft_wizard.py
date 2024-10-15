from odoo import models, fields


class ResetToDraftWizard(models.TransientModel):
    _name = 'reset.to.draft.wizard'
    _description = 'Reset To Draft Wizard'

    name = fields.Char(string='Name')

    def action_reset_to_draft(self):
        current_move_id = self.env.context.get('current_move_id')
        if current_move_id:
            move = self.env['account.move'].browse(current_move_id)
            move.reset_button_draft()
