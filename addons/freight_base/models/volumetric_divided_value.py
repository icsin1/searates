# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class VolumetricDividedValue(models.Model):
    _name = 'volumetric.divided.value'
    _description = 'Volumetric Divided Value'

    transport_mode_id = fields.Many2one('transport.mode', string="Transport Mode")
    uom_id = fields.Many2one('uom.uom', string="UOM")
    divided_value = fields.Float(string="Divided Value")

    @api.constrains("transport_mode_id", "uom_id", "divided_value")
    def _check_divided_value(self):
        for rec in self:
            if rec.divided_value < 0:
                raise ValidationError("Divided value can't be Negative")
            volumetric_divided_value = self.env['volumetric.divided.value'].search_count([('transport_mode_id', '=', rec.transport_mode_id.id),
                            ('uom_id', '=', rec.uom_id.id),
                            ('id', '!=', rec.id)
                            ])
            if volumetric_divided_value:
                raise UserError(
                    ("Divided value for '%s' transport mode and '%s' unit of measure already exists.")
                    %(rec.transport_mode_id.name, rec.uom_id.name)
                )
