from odoo import _, api, models
from odoo.exceptions import ValidationError


class PaymentLinkWizard(models.TransientModel):
    _inherit = "payment.link.wizard"

    @api.onchange('amount', 'description')
    def _onchange_amount(self):
        move = self.env[self.res_model].browse(self.res_id)
        if self.amount <= 0 and move.payment_state == 'paid':
            move_type_label = dict(move.fields_get()['move_type']['selection']).get(move.move_type)
            raise ValidationError(_(f"You can not generate a payment link for a paid {move_type_label}"))
        super()._onchange_amount()
