from odoo import fields, models, api


class FreightEventType(models.Model):
    _name = "freight.event.type"
    _description = 'Freight Event Type'
    _order = 'sequence'
    _rec_name = 'display_name'

    display_name = fields.Char(compute='_compute_display_name', store=True)
    code = fields.Char(string='Event Code', copy=False, required=True)
    name = fields.Char(string='Event Name', required=True)
    sequence = fields.Integer(default=10)
    description = fields.Text()
    public_visible = fields.Boolean(string='Public Visible', default=False)

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code must be unique !')
    ]

    @api.depends("name", "code")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '[{}] {}'.format(rec.code, rec.name)
