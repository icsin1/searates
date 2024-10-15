# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FreightLocationType(models.Model):
    _name = "freight.location.type"
    _description = "Freight Location Type"

    name = fields.Char(required=True, default='New', copy=False)
    active = fields.Boolean(default=True)

    @api.constrains('name')
    def _check_name(self):
        for rec in self:
            other_location_type = self.search(
                [('name', '=ilike', rec.name), ('id', '!=', rec.id)], limit=1)
            if other_location_type:
                raise ValidationError(_("Name:%s already exists in the system!") % (other_location_type.name))
