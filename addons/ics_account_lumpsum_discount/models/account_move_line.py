from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    lumpsum_discount = fields.Float(string='Discount')

    @api.onchange('lumpsum_discount', 'quantity', 'price_unit')
    def _onchange_lumpsum_discount(self):
        if self.price_unit and self.quantity:
            self.discount = (self.lumpsum_discount * 100) / (self.price_unit * self.quantity)

    @api.onchange('discount', 'quantity', 'price_unit')
    def _onchange_discount(self):
        if self.price_unit and self.quantity:
            self.lumpsum_discount = (self.price_unit * self.quantity) * (self.discount / 100)
