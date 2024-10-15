# -*- coding: utf-8 -*-
from odoo import models, fields, api


class FreightShipmentPackage(models.Model):
    _inherit = 'freight.house.shipment.package'
    _description = 'Shipment Package'

    quote_cargo_line_id = fields.Many2one('shipment.quote.cargo.lines', copy=False)
    quote_container_line_id = fields.Many2one('shipment.quote.container.lines', copy=False)

    @api.model_create_single
    def create(self, values):
        package = super().create(values)
        # set packages/Container reference from shipment to quote
        if package.quote_cargo_line_id:
            package.quote_cargo_line_id.pack_container_id = package.id
        if package.quote_container_line_id:
            package.quote_container_line_id.pack_container_id = package.id
        return package
