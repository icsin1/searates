# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ResCurrency(models.Model):
    _name = "res.currency"
    _inherit = ['res.currency', 'mail.thread', 'mail.activity.mixin']

    is_fixed_rate_currency = fields.Boolean(
        'Enable Fixed Rate', help="If Currency marked as Fixed-Rate, Manually entered amount will be considered as Exchange rate", tracking=1, company_dependent=True)
    fixed_rate = fields.Float('Fixed Rate', default=1.0, tracking=1, company_dependent=True)
    fetch_exchange_rate = fields.Boolean('Fetch exchange Rate', tracking=1, company_dependent=True)

    @api.depends('rate_ids.rate', 'is_fixed_rate_currency', 'fixed_rate')
    def _compute_current_rate(self):
        # When fixed rate enabled - change currency rate field values
        super()._compute_current_rate()
        company = self.env['res.company'].browse(self._context.get('company_id')) or self.env.company
        for currency in self.with_company(company).filtered(lambda c: c.is_fixed_rate_currency and c.fixed_rate):
            currency.rate = 1 / (currency.fixed_rate or 1.0)
            currency.inverse_rate = currency.fixed_rate
            if currency != company.currency_id:
                currency.rate_string = '1 %s = %.6f %s' % (company.currency_id.name, currency.rate, currency.name)
            else:
                currency.rate_string = ''

    def _get_rates(self, company, date):
        # Consider Fixed rate only in case of Fixed exchange-rate enabled
        if not self.ids:
            return {}
        currency_rates = super()._get_rates(company, date)
        for currency in self.with_company(company=company).filtered(lambda c: c.is_fixed_rate_currency and c.fixed_rate):
            currency_rates.update({currency.id: currency.rate})
        return currency_rates
