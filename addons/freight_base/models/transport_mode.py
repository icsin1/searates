from odoo import models, fields, api


class TransportMode(models.Model):
    _name = 'transport.mode'
    _description = 'Transport Mode'
    _order = 'sequence'
    _rec_name = 'display_name'

    display_name = fields.Char(compute="_compute_display_name", store=True)
    name = fields.Char(required=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    description = fields.Text()
    mode_type = fields.Selection([
        ('sea', 'Sea'),
        ('land', 'Land'),
        ('air', 'Air')
    ])
    active = fields.Boolean(default=True)
    allowed_route_mode_ids = fields.Many2many('transport.mode', 'route_transport_mode_rel', 'transport_mode_id', 'route_transport_mode_id', string='Allowed For Route', copy=False)

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code must be unique !')
    ]

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '[{}] {}'.format(rec.code, rec.name)
