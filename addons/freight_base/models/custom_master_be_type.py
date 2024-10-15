
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CustomMasterBeType(models.Model):
    _name = 'custom.master.be.type'
    _description = 'Custom BE Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True, tracking=True)

    @api.constrains('name')
    def _check_duplicate_be_type_name(self):
        custom_master_be_type_obj = self.env['custom.master.be.type']
        for rec in self:
            if custom_master_be_type_obj.search_count([('name', '=', rec.name)]) > 1:
                raise ValidationError(_("Name should be unique."))
