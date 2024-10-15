# -*- coding: utf-8 -*-
from odoo import api, fields, models
from itertools import groupby


class ResCurrencyRate(models.Model):
    _name = "res.currency.rate"
    _inherit = ["res.currency.rate", "mail.thread"]

    rate = fields.Float(tracking=True)
    provider_id = fields.Many2one('res.currency.rate.provider', string="Provider", ondelete="restrict")

    @api.model_create_multi
    def create(self, vals_list):
        # Create the new records
        records = super(ResCurrencyRate, self).create(vals_list)

        # Log the creation of new rates
        for currency_id, rates in groupby(records, key=lambda r: r.currency_id):
            currency_rates = self.concat(*rates)
            rates_message = "New currency rate added\n"
            for currency_rate in currency_rates.filtered(lambda cr: cr.rate):
                rates_message += f"for <b>{currency_rate.company_id.display_name}</b>: {currency_rate.rate}\n"
            currency_id.message_post(body=rates_message)
        return records

    def write(self, vals):
        """Unset link to provider in case 'rate' or 'name' are manually changed"""
        if ("rate" in vals or "name" in vals) and "provider_id" not in vals:
            vals["provider_id"] = False

        # Get old values before writing new ones
        old_rates = {rec.id: rec.rate for rec in self}

        # Call the super method to write the new values
        result = super(ResCurrencyRate, self).write(vals)

        # Post a message in the related res.currency model if the rate has changed
        for rec in self:
            if 'rate' in vals and rec.rate != old_rates[rec.id]:
                message = f"Currency rate changed for <b>{rec.company_id.display_name}</b> from {old_rates[rec.id]} to {rec.rate}"
                rec.currency_id.message_post(body=message)

        return result