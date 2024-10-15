from odoo import models, fields


class ResPartnerType(models.Model):
    _name = 'res.partner.type'
    _description = 'Partner Type'

    name = fields.Char(required=True)
    field_mapping_ids = fields.One2many('res.partner.type.field', 'type_id', string='Field Mapping')
    is_vendor = fields.Boolean(copy=False)
    color = fields.Integer(default=2)
    code = fields.Char()

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code must be unique !')
    ]


class PartnerCategoryFieldLine(models.Model):
    _name = "res.partner.type.field"
    _description = "Partner Type Field Line"

    type_id = fields.Many2one('res.partner.type', string='Type', ondelete="cascade")
    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete="cascade")
    field_id = fields.Many2one('ir.model.fields', string='Model Field', required=True, ondelete="cascade")
