# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class FreightTruckNumber(models.Model):
    _name = "freight.truck.trailer.number"
    _description = 'Freight Truck Trailer Number'

    name = fields.Char(required=True, default='New', copy=False)

    @api.constrains('name')
    def _check_name(self):
        for rec in self:
            other_trailer_number = self.search(
                [('name', '=ilike', rec.name), ('id', '!=', rec.id)], limit=1)
            if other_trailer_number:
                raise ValidationError(_("Name:%s already exists in the system!") % (other_trailer_number.name))
