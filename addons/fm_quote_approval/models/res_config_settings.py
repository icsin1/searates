# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    margin_percent = fields.Float(string='Margin Percent', readonly=False, related='company_id.margin_percent')
    margin_revenue = fields.Monetary(string='Margin Revenue', readonly=False, related='company_id.margin_revenue')

    @api.constrains("margin_percent", "margin_revenue")
    def _check_margin_percent_revenue(self):
        for rec in self:
            if rec.margin_percent < 0 and rec.margin_revenue < 0:
                raise ValidationError(
                    _("Margin Percentage and Margin Revenue should be positive value")
                )
            elif rec.margin_percent < 0:
                raise ValidationError(
                    _("Margin Percentage should be positive value")
                )
            elif rec.margin_revenue < 0:
                raise ValidationError(
                    _("Margin Revenue should be positive value")
                )
