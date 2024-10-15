# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class TruckType(models.Model):
    _name = "truck.type"
    _description = 'Truck Type'

    name = fields.Char(required=True, default='New', copy=False)
    active = fields.Boolean(default=True)

    @api.constrains('name')
    def _check_name(self):
        for rec in self:
            truck_type = self.search(
                [('name', '=ilike', rec.name), ('id', '!=', rec.id)], limit=1)
            if truck_type:
                raise ValidationError(_("Truck Type:%s already exists in the system!") % (truck_type.name))
