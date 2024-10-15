# -*- coding: utf-8 -*-
from odoo import models, fields


class QuoteTransportationPackageDetails(models.Model):
    _name = 'quote.transportation.package.details'
    _inherit = ['quote.transportation.details', 'shipment.quote.container.lines', 'shipment.quote.cargo.lines']
    _description = "Quote Transportation Package Details"

    quote_for = fields.Selection(related='quotation_id.quote_for')
    is_package_group = fields.Boolean(related="quotation_id.is_package_group")
    container_type_id = fields.Many2one('freight.container.type', required=False, string="Truck Type")
    is_refrigerated = fields.Boolean(related='container_type_id.category_id.is_refrigerated', store=True)
    container_temperature = fields.Float(string="Min Temperature")
    container_temperature_uom_id = fields.Many2one('uom.uom', domain=lambda self: [
        ('category_id', '=', self.env.ref('freight_base.product_uom_categ_temperature').id)])
    max_temperature = fields.Float(string="Max Temperature")
    max_temperature_uom_id = fields.Many2one('uom.uom', domain=lambda self: [('category_id', '=', self.env.ref('freight_base.product_uom_categ_temperature').id)])
    length = fields.Float()
    width = fields.Float()
    height = fields.Float()
    lwh_uom_id = fields.Many2one('uom.uom', domain=lambda self: [('category_id', '=', self.env.ref('uom.uom_categ_length').id)], ondelete="restrict")
    calculated_dimension_lwh = fields.Boolean(related='quotation_id.cargo_type_id.calculated_dimension_lwh', store=True)
    divided_value = fields.Float(string="Divided Value", store=True)
    transport_mode_id = fields.Many2one('transport.mode', related='quotation_id.transport_mode_id', store=True)
