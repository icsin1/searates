# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class OpportunityTransportationDetails(models.Model):
    _name = 'opportunity.transportation.details'
    _inherit = ['freight.transport.mixin', 'crm.prospect.opportunity.package', 'crm.prospect.opportunity.container']
    _description = "Opportunity Transportation Details"

    @api.depends('estimated_pickup', 'expected_delivery')
    def _compute_transit_time(self):
        for rec in self:
            transit_time = 0
            if rec.expected_delivery and rec.estimated_pickup:
                transit_time = (rec.expected_delivery - rec.estimated_pickup).days
            rec.transit_time = transit_time

    estimated_pickup = fields.Date('ETP')
    expected_delivery = fields.Date('ETD')
    transit_time = fields.Integer('TT(In days)', compute='_compute_transit_time', store=True, readonly=False)
    container_type_id = fields.Many2one("freight.container.type", string="Truck Type", required=False)
    is_refrigerated = fields.Boolean(related='container_type_id.category_id.is_refrigerated', store=True)
    container_temperature = fields.Float(string="Min Temperature")
    container_temperature_uom_id = fields.Many2one('uom.uom', domain=lambda self: [
        ('category_id', '=', self.env.ref('freight_base.product_uom_categ_temperature').id)])
    max_temperature = fields.Float(string="Max Temperature")
    max_temperature_uom_id = fields.Many2one('uom.uom', domain=lambda self: [('category_id', '=', self.env.ref('freight_base.product_uom_categ_temperature').id)])
    length = fields.Float()
    width = fields.Float()
    height = fields.Float()
    lwh_uom_id = fields.Many2one(
        'uom.uom', domain=lambda self: [('category_id', '=', self.env.ref('uom.uom_categ_length').id)], ondelete="restrict")
    divided_value = fields.Float(string="Divided Value")
    calculated_dimension_lwh = fields.Boolean(related='opportunity_id.cargo_type_id.calculated_dimension_lwh', store=True)
    transport_mode_id = fields.Many2one(related='opportunity_id.transport_mode_id', store=True)

    @api.onchange('lwh_uom_id', 'transport_mode_id')
    def _onchange_divided_value(self):
        if self.transport_mode_id and self.lwh_uom_id:
            volumetric_divided_value = self.env['volumetric.divided.value'].search([
                ('transport_mode_id', '=', self.transport_mode_id.id),
                ('uom_id', '=', self.lwh_uom_id.id)
            ])
            if volumetric_divided_value.divided_value:
                self.divided_value = volumetric_divided_value.divided_value
            else:
                raise UserError(_("Divided value for '%s' transport mode and '%s' UOM is not defined.") % (self.transport_mode_id.name, self.lwh_uom_id.name))

    @api.constrains('estimated_pickup', 'expected_delivery')
    def _check_shipment_pickup_delivery_date(self):
        for record in self:
            if record.estimated_pickup and record.expected_delivery and (
                    record.estimated_pickup > record.expected_delivery):
                raise ValidationError(_(
                    'Estimated Pickup date should be less than Estimated Delivery Date.'))
