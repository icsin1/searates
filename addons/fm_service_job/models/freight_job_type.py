# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FreightJobType(models.Model):
    _name = 'freight.job.type'
    _description = 'Freight Job Type'
    _order = 'name asc'

    name = fields.Char(string='Service Job Type', required=True, copy=False)
    active = fields.Boolean(default=True)

    @api.constrains('name')
    def _check_job_type(self):
        for rec in self:
            duplicate_job_type = self.search([('name', '=ilike', rec.name), ('id', '!=', rec.id)], limit=1)
            if duplicate_job_type:
                raise ValidationError(_("Service Job Type:%s already exists in the system!") % (duplicate_job_type.name))

    def unlink(self):
        try:
            res = super().unlink()
        except Exception:
            raise ValidationError(_('You can not remove Freight Job Type which is already in use.'))
        return res
