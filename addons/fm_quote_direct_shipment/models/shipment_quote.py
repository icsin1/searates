# -*- coding: utf-8 -*-
from odoo import models, fields


class ShipmentQuote(models.Model):
    _inherit = "shipment.quote"

    create_shipment_for = fields.Selection(related='company_id.create_shipment_for', store=True)

    def action_create_direct_shipment(self):
        if self.create_shipment_for == 'house_shipment':
            if self.multi_carrier_quote:
                return self.with_context(from_direct_shipment=True).action_quote_multi_carrier_shipment()
            action = self.action_create_shipment()
            context = action['context'].copy()
            context.update({'default_is_quote_direct_shipment': True, 'default_is_direct_shipment': True})
            action['context'] = context
            return action
        return super().action_create_direct_shipment()

    def _compute_freight_shipment_type(self):
        super()._compute_freight_shipment_type()
        for quote in self:
            if quote.create_shipment_for == 'house_shipment' and any(shipment.is_quote_direct_shipment for shipment in quote.freight_shipment_ids):
                quote.freight_shipment_type = 'master_shipment'
