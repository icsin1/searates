# -*- coding: utf-8 -*-

from odoo import models, fields


class ShipmentQuoteLine(models.Model):
    _inherit = "shipment.quote.line"

    multi_carrier_quote = fields.Boolean(related='quotation_id.multi_carrier_quote', store=True)
    carrier_id = fields.Many2one('freight.carrier', string='Shipping Line')
    incoterm_id = fields.Many2one('account.incoterms', string='Incoterms')
    transport_mode_id = fields.Many2one(related='quotation_id.transport_mode_id', store=True)
    mode_type = fields.Selection(related='quotation_id.mode_type', store=True)
