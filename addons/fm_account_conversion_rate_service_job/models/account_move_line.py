# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.onchange('amount_currency', 'currency_id')
    def _onchange_amount_currency_and_currency(self):
        for line in self.filtered(
                lambda move_line: not move_line.house_shipment_id and not move_line.master_shipment_id):
            line.currency_exchange_rate = line.currency_id._get_conversion_rate(line.currency_id,
                                                                                line.move_id.company_id.currency_id,
                                                                                line.move_id.company_id,
                                                                                line.move_id.date or fields.Date.context_today(
                                                                                    line))

    @api.model_create_multi
    def create(self, vals_list):
        lines = super(AccountMoveLine, self.with_context(service_job_model=True)).create(vals_list)
        for line in lines.filtered(
                lambda move_line: not move_line.currency_exchange_rate and not move_line.house_shipment_id and not move_line.master_shipment_id and not move_line.service_job_id):
            line.currency_exchange_rate = line.currency_id._get_conversion_rate(line.currency_id,
                                                                                line.move_id.company_id.currency_id,
                                                                                line.move_id.company_id,
                                                                                line.move_id.date or fields.Date.context_today(
                                                                                    line))
        return lines

    def write(self, vals_list):
        res = super(AccountMoveLine, self.with_context(service_job_model=True)).write(vals_list)
        for line in self.filtered(
                lambda move_line: not move_line.house_shipment_id and not move_line.master_shipment_id and not move_line.service_job_id):
            if 'currency_id' in vals_list:
                line.currency_exchange_rate = line.currency_id._get_conversion_rate(line.currency_id,
                                                                                    line.move_id.company_id.currency_id,
                                                                                    line.move_id.company_id,
                                                                                    line.move_id.date or fields.Date.context_today(
                                                                                        line))
        return res

    def _compute_amount_residual(self):
        res = super(AccountMoveLine, self)._compute_amount_residual()
        for line in self.move_id.line_ids.filtered(lambda move_line: not move_line.house_shipment_id and not move_line.master_shipment_id and not move_line.service_job_id):
            currency_exchange_rate = line.currency_id._get_conversion_rate(
                line.currency_id,
                line.move_id.company_id.currency_id,
                line.move_id.company_id,
                line.move_id.date or fields.Date.context_today(line))
            if line.currency_exchange_rate == currency_exchange_rate:
                line.with_context(check_move_validity=False).currency_exchange_rate = currency_exchange_rate
            else:
                line.currency_exchange_rate = currency_exchange_rate
        return res
