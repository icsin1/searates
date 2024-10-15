# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import json


class ShipmentQuoteCargoLines(models.Model):
    _name = "shipment.quote.cargo.lines"
    _description = "Shipment Quote Cargo Lines"

    @api.model
    def get_default_pack_type(self):
        return self.env.company.pack_uom_id.id

    @api.model
    def get_default_weight_uom(self):
        return self.env.company.weight_uom_id.id

    @api.model
    def get_default_volume_uom(self):
        return self.env.company.volume_uom_id.id

    @api.depends('transport_mode_id')
    def _compute_pack_type_domain(self):
        for rec in self:
            domain = ['|', ('transport_mode_ids', '=', rec.transport_mode_id.id), ('transport_mode_ids', '=', False), ('category_id', '=', self.env.ref('freight_base.product_uom_categ_pack').id)]
            rec.pack_type_domain = json.dumps(domain)

    pack_type_domain = fields.Char(compute='_compute_pack_type_domain', store=True)
    quotation_id = fields.Many2one('shipment.quote', required=True, ondelete='cascade', copy=False)
    transport_mode_id = fields.Many2one(related='quotation_id.transport_mode_id', store=True)
    mode_type = fields.Selection(related='transport_mode_id.mode_type', store=True)
    count = fields.Integer(string='Count', required=True)
    pack_type_id = fields.Many2one(
        'uom.uom', string='Pack Type', required=True, default=get_default_pack_type)
    volumetric_divider_value = fields.Integer(related="quotation_id.company_id.volumetric_divider_value")
    volumetric_weight = fields.Float(string="Volumetric Weight", readonly=False, compute="_compute_volumetric_weight", store=True)
    volumetric_weight_uom_id = fields.Many2one(
        'uom.uom', default=get_default_weight_uom, domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)], ondelete="restrict")
    weight_uom_id = fields.Many2one('uom.uom', string='Weight UoM', default=get_default_weight_uom,
                                    domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)], ondelete="restrict")
    weight = fields.Float(string='Weight')
    volume_uom_id = fields.Many2one('uom.uom', string='Volume UoM', default=get_default_volume_uom,
                                    domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_vol').id)], ondelete="restrict")
    volume = fields.Float(string='Volume', readonly=False)
    commodity_id = fields.Many2one('freight.commodity')
    commodity_hs_code = fields.Char(string='HS Code')
    is_hazardous = fields.Boolean(string="Is HAZ", default=False)
    notes = fields.Text(string='Goods Description')
    pack_container_id = fields.Many2one('freight.house.shipment.package', copy=False)
    length = fields.Float()
    width = fields.Float()
    height = fields.Float()
    cargo_type_id = fields.Many2one(related='quotation_id.cargo_type_id', store=True)
    cargo_code = fields.Char(related='cargo_type_id.code', store=True)
    calculated_dimension_lwh = fields.Boolean(related='cargo_type_id.calculated_dimension_lwh', store=True)

    lwh_uom_id = fields.Many2one(
        'uom.uom', domain=lambda self: [('category_id', '=', self.env.ref('uom.uom_categ_length').id)], ondelete="restrict")
    divided_value = fields.Float(string="Divided Value")
    chargeable_volume = fields.Float(string='Chargeable Volume')
    chargeable_uom_id = fields.Many2one('uom.uom', string='Volume UoM', default=get_default_volume_uom,
                                        domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_vol').id)], ondelete="restrict")

    @api.onchange('length', 'width', 'height', 'count', 'divided_value', 'lwh_uom_id', 'weight', 'volume', 'chargeable_volume')
    def _onchange_sea_volumetric_weight(self):
        for rec in self:
            if rec.mode_type == 'sea':
                if rec.divided_value:
                    rec.volume = (rec.count * rec.length * rec.width * rec.height) / rec.divided_value
                    if rec.weight:
                        weight = (rec.weight / 1000)
                        rec.chargeable_volume = max(rec.volume, weight)
                    else:
                        rec.chargeable_volume = 0.0
                else:
                    rec.volume = 0.0

    @api.depends('length', 'width', 'height', 'count', 'divided_value', 'lwh_uom_id')
    def _compute_volumetric_weight(self):
        for rec in self:
            if rec.mode_type in ['air', 'land']:
                if not rec.divided_value:
                    rec.volumetric_weight = 0
                else:
                    rec.volumetric_weight = (rec.length * rec.width * rec.height * rec.count) / rec.divided_value
            else:
                rec.volumetric_weight = rec.volumetric_weight

    @api.onchange('lwh_uom_id', 'transport_mode_id')
    def _onchange_uom_transport_mode(self):
        self.divided_value = 0
        if self.transport_mode_id and self.lwh_uom_id:
            volumetric_divided_value = self.env['volumetric.divided.value'].search([
                ('transport_mode_id', '=', self.transport_mode_id.id),
                ('uom_id', '=', self.lwh_uom_id.id)
                ])
            if not volumetric_divided_value:
                raise UserError(
                    ("Divided value for '%s' transport mode and '%s' UOM is not defined.")
                    %(self.transport_mode_id.name, self.lwh_uom_id.name)
                    )
            self.divided_value = volumetric_divided_value.divided_value

    @api.onchange('commodity_id')
    def _onchange_commodity_id(self):
        for rec in self:
            rec.commodity_hs_code = rec.commodity_id.hs_code_id and rec.commodity_id.hs_code_id.code or False
            rec.is_hazardous = rec.commodity_id.hazardous

    @api.onchange('count')
    def check_count(self):
        if self.count < 0:
            raise ValidationError('Package count should not be negative.')
