# -*- coding: utf-8 -*-
from odoo import fields, models


class ShippingLineFreeTime(models.Model):
    _name = "shipping.line.free.time"
    _description = "Shipping Line Free Time"

    free_time = fields.Char(string='Free Time')
    origin = fields.Integer(string='Origin')
    destination = fields.Integer(string='Destination')
    shipment_quote_id = fields.Many2one('shipment.quote', string='Shipment Quote')
