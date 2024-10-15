# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class OpportunityPackage(models.Model):
    _name = "crm.prospect.opportunity.package"
    _description = "Opportunity Package"

    @api.model
    def get_default_volume_uom(self):
        return self.env.company.volume_uom_id.id

    @api.model
    def get_default_package_uom(self):
        return self.env.company.pack_uom_id.id

    @api.model
    def get_default_weight_uom(self):
        return self.env.company.weight_uom_id.id

    @api.model
    def get_default_dimension_uom(self):
        return self.env.company.dimension_uom_id.id

    opportunity_id = fields.Many2one("crm.prospect.opportunity", string="Linked Opportunity", required=True, ondelete='cascade')
    quantity = fields.Integer("No Of Packages", required=True)
    package_uom_id = fields.Many2one("uom.uom", string="Package UoM", required=True, default=get_default_package_uom,
                                     domain=lambda self: [('category_id', '=', self.env.ref('freight_base.product_uom_categ_pack').id)])

    weight = fields.Float(required=True)
    weight_uom_id = fields.Many2one("uom.uom", string="Weight UoM", required=True, default=get_default_weight_uom,
                                    domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)])
    volume = fields.Float(required=True)
    volume_uom_id = fields.Many2one("uom.uom", string="Volume UoM", required=True, default=get_default_volume_uom,
                                    domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_vol').id)])
    total_weight = fields.Float(required=True)
    total_weight_uom_id = fields.Many2one("uom.uom", string="Total Weight UoM", required=True, default=get_default_weight_uom,
                                          domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)])
    total_volume = fields.Float(required=True)
    total_volume_uom_id = fields.Many2one("uom.uom", string="Total Volume UoM", required=True, default=get_default_volume_uom,
                                          domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_vol').id)])

    length = fields.Float()
    width = fields.Float()
    height = fields.Float()
    divided_value = fields.Float(string="Divided Value")
    cargo_type_id = fields.Many2one(related='opportunity_id.cargo_type_id', store=True)
    cargo_code = fields.Char(related='cargo_type_id.code', store=True)
    calculated_dimension_lwh = fields.Boolean(related='cargo_type_id.calculated_dimension_lwh', store=True)
    transport_mode_id = fields.Many2one(related='opportunity_id.transport_mode_id', store=True)
    mode_type = fields.Selection(related='transport_mode_id.mode_type', store=True)
    lwh_uom_id = fields.Many2one(
        'uom.uom', domain=lambda self: [('category_id', '=', self.env.ref('uom.uom_categ_length').id)], ondelete="restrict")

    @api.onchange('lwh_uom_id', 'transport_mode_id')
    def _onchange_divided_value_field(self):
        if self.transport_mode_id and self.lwh_uom_id:
            volumetric_divided_value = self.env['volumetric.divided.value'].search([
                ('transport_mode_id', '=', self.transport_mode_id.id),
                ('uom_id', '=', self.lwh_uom_id.id)
            ])
            if volumetric_divided_value.divided_value:
                self.divided_value = volumetric_divided_value.divided_value
            else:
                raise UserError(_("Divided value for '%s' transport mode and '%s' UOM is not defined.") % (self.transport_mode_id.name, self.lwh_uom_id.name))
