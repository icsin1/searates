# -*- coding: utf-8 -*-

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    margin_percent = fields.Float(string='Margin Percent')
    margin_revenue = fields.Monetary(string='Margin Revenue')
