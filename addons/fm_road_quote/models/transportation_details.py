# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class QuoteTransportationDetails(models.Model):
    _name = "quote.transportation.details"
    _inherit = ['freight.transport.mixin']
    _description = "Quote Transportation Details"

    @api.depends('estimated_pickup', 'expected_delivery')
    def _compute_transit_time(self):
        for rec in self:
            transit_time = 0
            if rec.expected_delivery and rec.estimated_pickup:
                transit_time = (rec.expected_delivery - rec.estimated_pickup).days
            rec.transit_time = transit_time

    shipment_quote_id = fields.Many2one('shipment.quote')
    estimated_pickup = fields.Date("ETP")
    expected_delivery = fields.Date("ETD")
    transit_time = fields.Integer('TT(In days)', compute='_compute_transit_time', store=True, readonly=False)

    @api.constrains('estimated_pickup', 'expected_delivery')
    def _check_shipment_pickup_delivery_date(self):
        for record in self:
            if record.estimated_pickup and record.expected_delivery and (
                    record.estimated_pickup > record.expected_delivery):
                raise ValidationError(_(
                    'Estimated Pickup date should be less than Estimated Delivery Date.'))
