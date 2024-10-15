# -*- coding: utf-8 -*-

from odoo import models, api


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency, company, date):
        res = super()._get_conversion_rate(from_currency, to_currency, company, date)
        currency_rates = (from_currency + to_currency)._get_rates(company, date)
        from_currency_amt = currency_rates.get(from_currency.id)
        if from_currency != to_currency and self.env.context.get('currency_exchange_rate'):
            currency_exchange_rate = self.env.context.get('currency_exchange_rate')
            res = currency_exchange_rate if to_currency.id == company.currency_id.id else from_currency_amt / currency_exchange_rate
        return res
