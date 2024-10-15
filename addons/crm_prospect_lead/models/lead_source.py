# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class LeadSource(models.Model):
    _name = "lead.source"
    _description = "Lead Source"

    name = fields.Char(string='Name')
    sequence = fields.Integer(default=99)
    allow_source_creation = fields.Boolean(string='Allow Source Creation', default=True)

    @api.constrains('name')
    def _unique_name(self):
        lead_source_name = self.search_count([('name', '=', self.name), ('id', '!=', self.id)])
        if lead_source_name > 0:
            raise ValidationError(_("'%s' name already exists!", self.name))
