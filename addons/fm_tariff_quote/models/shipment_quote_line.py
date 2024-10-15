# -*- coding: utf-8 -*-
from odoo import fields, models


class ShipmentQuoteLine(models.Model):
    _inherit = "shipment.quote.line"

    buy_tariff_line_id = fields.Many2one('tariff.buy.line')
    sell_tariff_line_id = fields.Many2one('tariff.sell.line')
