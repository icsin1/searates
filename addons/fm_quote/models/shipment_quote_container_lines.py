# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ShipmentQuoteContainerLines(models.Model):
    _name = "shipment.quote.container.lines"
    _description = "Shipment Quote Container Lines"

    quotation_id = fields.Many2one('shipment.quote', required=True, ondelete='cascade', copy=False)
    count = fields.Integer(string='Count', required=True, default=1)
    container_type_code = fields.Char(string='Container Type Code')
    container_type_id = fields.Many2one('freight.container.type', required=True)
    teu = fields.Integer(string='TEU', compute='_compute_teu', store=True, readonly=False)
    commodity = fields.Many2one('freight.commodity', string='Commodity')
    pack_container_id = fields.Many2one('freight.house.shipment.package', copy=False)
    transport_mode_id = fields.Many2one('transport.mode', related='quotation_id.transport_mode_id', store=True)

    @api.onchange('count')
    def check_count(self):
        if self.count < 0:
            raise ValidationError('Package count should not be negative.')

    @api.depends('container_type_id', 'count')
    def _compute_teu(self):
        for rec in self:
            rec.teu = rec.count * rec.container_type_id.total_teu
