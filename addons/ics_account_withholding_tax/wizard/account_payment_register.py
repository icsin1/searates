# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    withholding_tax_id = fields.Many2one('account.tax')

    def _create_payment_vals_from_wizard(self):
        payment_vals = super()._create_payment_vals_from_wizard()
        if self.withholding_tax_id:
            payment_vals['withholding_tax_id'] = self.withholding_tax_id.id
        return payment_vals
