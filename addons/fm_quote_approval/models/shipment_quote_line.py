# -*- coding: utf-8 -*-
from odoo import fields, models


class ShipmentQuoteLine(models.Model):
    _inherit = "shipment.quote.line"

    is_margin_percent = fields.Boolean(string="Is Margin Percentage ?", related="quotation_id.is_margin_percent")
