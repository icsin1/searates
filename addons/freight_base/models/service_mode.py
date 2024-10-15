from odoo import models, fields, api


class FreightServiceMode(models.Model):
    _name = 'freight.service.mode'
    _description = 'Service Mode'
    _order = 'sequence'
    _rec_name = 'display_name'

    display_name = fields.Char(compute="_compute_display_name", store=True)
    name = fields.Char(required=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    description = fields.Text()
    active = fields.Boolean(default=True)

    # Configurations fields
    have_main_carriage = fields.Boolean(default=False)

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code must be unique !')
    ]

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '[{}] {}'.format(rec.code, rec.name)
