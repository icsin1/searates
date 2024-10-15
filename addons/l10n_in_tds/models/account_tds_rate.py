# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountTdsRate(models.Model):
    _name = "account.tds.rate"
    _description = "TDS Rate"

    name = fields.Char(required=True)
    rate_percentage = fields.Float(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    country_id = fields.Many2one('res.country', required=True, related='company_id.country_id', store=True,
                                 readonly=False)
