# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    account_tds_rate_id = fields.Many2one('account.tds.rate', string="TDS Rate", copy=False)
    tds_amount = fields.Monetary(string='TDS Amount', store=True, compute='cal_account_tds_rate_amount', currency_field='currency_id')
    is_tds_line = fields.Boolean(string="TDS Line", copy=False)

    @api.depends('account_tds_rate_id', 'price_subtotal')
    def cal_account_tds_rate_amount(self):
        for rec in self:
            rec.tds_amount = (rec.account_tds_rate_id.rate_percentage * rec.price_subtotal) / 100 \
                if rec.account_tds_rate_id else 0.00

    def copy_data(self, default=None):
        res = super(AccountMoveLine, self).copy_data(default=default)
        if 'move_reverse_cancel' in self.env.context:
            for line, values in zip(self, res):
                values.update({
                    'is_tds_line': line.is_tds_line,
                    'account_tds_rate_id': line.account_tds_rate_id.id
                    })
        return res
