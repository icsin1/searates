# -*- coding: utf-8 -*-

from odoo import models, fields


class ShipmentTransportationDetails(models.Model):
    _inherit = 'freight.shipment.transportation.details'

    is_refrigerated = fields.Boolean(related='container_type_id.category_id.is_refrigerated', store=True, string="Is Refrigerated")
    container_temperature = fields.Float(string="Min Temperature")
    container_temperature_uom_id = fields.Many2one('uom.uom', domain=lambda self: [
        ('category_id', '=', self.env.ref('freight_base.product_uom_categ_temperature').id)])
    max_temperature = fields.Float(string="Max Temperature")
    max_temperature_uom_id = fields.Many2one('uom.uom', domain=lambda self: [('category_id', '=', self.env.ref('freight_base.product_uom_categ_temperature').id)])
