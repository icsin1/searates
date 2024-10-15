# -*- coding: utf-8 -*-

from odoo import models, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _get_fields_onchange_subtotal(self, price_subtotal=None, move_type=None, currency=None, company=None, date=None):
        return super(AccountMoveLine, self.with_context(
            currency_exchange_rate=self.move_id.currency_exchange_rate
        ))._get_fields_onchange_subtotal(price_subtotal, move_type, currency, company, date)

    @api.onchange('amount_currency')
    def _onchange_amount_currency(self):
        super(AccountMoveLine, self.with_context(
            currency_exchange_rate=self.move_id.currency_exchange_rate
        ))._onchange_amount_currency()
