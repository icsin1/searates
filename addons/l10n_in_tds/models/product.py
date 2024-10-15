# -*- coding: utf-8 -*-

from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    income_tds_rate_id = fields.Many2one('account.tds.rate', string="Income TDS Rate", copy=False)
    expense_tds_rate_id = fields.Many2one('account.tds.rate', string="Expense TDS Rate", copy=False)
