# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    currency_exchange_rate = fields.Float('Ex.Rate', copy=False, digits='Currency Exchange Rate')

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        self.ensure_one()
        return super(AccountPayment, self.with_context(
            currency_exchange_rate=self.currency_exchange_rate
        ))._prepare_move_line_default_vals(write_off_line_vals)
