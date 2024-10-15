from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FreightCargoWeightVolumeMixin(models.AbstractModel):
    _name = 'freight.cargo.weight.volume.mixin'
    _description = 'Freight Cargo Weight-Volume Mixin'

    @api.model
    def get_default_pack_type(self):
        return self.env.company.pack_uom_id.id

    @api.model
    def get_default_weight_uom(self):
        return self.env.company.weight_uom_id.id

    @api.model
    def get_default_volume_uom(self):
        return self.env.company.volume_uom_id.id

    @api.depends('gross_weight_unit', 'gross_weight_unit_uom_id', 'net_weight_unit', 'net_weight_unit_uom_id', 'weight_volume_unit', 'weight_volume_unit_uom_id', 'chargeable_uom_id')
    def _compute_chargeable_kg(self):
        for rec in self:
            chargeable_uom = rec.chargeable_uom_id
            gross_weight = rec.gross_weight_unit_uom_id._compute_quantity(rec.gross_weight_unit, chargeable_uom) if chargeable_uom else rec.gross_weight_unit
            net_weight = rec.net_weight_unit_uom_id._compute_quantity(rec.net_weight_unit, chargeable_uom) if chargeable_uom else rec.net_weight_unit
            weight_volume = rec.weight_volume_unit_uom_id._compute_quantity(rec.weight_volume_unit, chargeable_uom) if chargeable_uom else rec.weight_volume_unit
            rec.chargeable_kg = round(max(gross_weight, net_weight, weight_volume, 0), 3) or rec.chargeable_kg

    pack_unit = fields.Integer('Packs', default=None)
    pack_unit_uom_id = fields.Many2one(
        'uom.uom', 'Packs UoM', domain=lambda self: [('category_id', '=', self.env.ref('freight_base.product_uom_categ_pack').id)], default=get_default_pack_type)

    net_weight_unit = fields.Float('Net Weight', default=None)
    net_weight_unit_uom_id = fields.Many2one(
        'uom.uom', 'Net Weight UoM', domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)], default=get_default_weight_uom)

    gross_weight_unit = fields.Float('Gross Weight', default=None)
    gross_weight_unit_uom_id = fields.Many2one(
        'uom.uom', 'Gross Weight UoM', domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)], default=get_default_weight_uom)

    volume_unit = fields.Float('Volume', default=0)
    volume_unit_uom_id = fields.Many2one(
        'uom.uom', 'Volume UoM', domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_vol').id)], default=get_default_volume_uom)

    weight_volume_unit = fields.Float('Volumetric Weight', default=None)
    weight_volume_unit_uom_id = fields.Many2one(
        'uom.uom', 'Volumetric Weight UoM', domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)], default=get_default_weight_uom)

    chargeable_kg = fields.Float(string='Chargeable ', compute='_compute_chargeable_kg', store=True)
    chargeable_uom_id = fields.Many2one(
        'uom.uom', domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)], default=get_default_weight_uom)

    @api.constrains('gross_weight_unit', 'net_weight_unit', 'gross_weight_unit_uom_id', 'net_weight_unit_uom_id')
    def _check_gross_net_weight_unit(self):
        for rec in self:
            net_weight = rec.net_weight_unit_uom_id._compute_quantity(rec.net_weight_unit, rec.gross_weight_unit_uom_id)
            # NEED TO ROUND VALUE, as after conversion it may contain some point value where this condition is failing
            if round(rec.gross_weight_unit) < round(net_weight):
                raise ValidationError(_('The Net weight should not be greater than the Gross weight.'))

    @api.onchange('pack_unit')
    def check_pack_unit(self):
        for rec in self:
            if rec.pack_unit < 0:
                raise ValidationError('Pack Unit should not be negative.')
