# -*- coding: utf-8 -*-

from odoo import models, fields


class ShipmentQuote(models.Model):
    _inherit = 'shipment.quote'

    generated_from_portal = fields.Boolean("Generated From Portal")

    def _compute_access_url(self):
        super()._compute_access_url()
        for quote in self:
            quote.access_url = '/dashboard/shipment_quote/%s' % (quote.id)
