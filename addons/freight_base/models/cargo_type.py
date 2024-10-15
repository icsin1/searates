from odoo import models, fields, api


class CargoType(models.Model):
    _name = 'cargo.type'
    _description = 'Cargo Type'
    _rec_name = 'display_name'
    _order = 'name'

    display_name = fields.Char(compute="_compute_display_name", store=True)
    name = fields.Char(required=True)
    code = fields.Char(required=True)
    transport_mode_id = fields.Many2one('transport.mode', required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    is_package_group = fields.Boolean(default=False)
    description = fields.Text()
    is_courier_shipment = fields.Boolean(default=False)
    calculated_dimension_lwh = fields.Boolean(default=False)

    _sql_constraints = [
        ('code_mode_uniq', 'unique (code,transport_mode_id)', 'The code must be unique per Transport Mode!')
    ]

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '[{}] {}'.format(rec.code, rec.name)
