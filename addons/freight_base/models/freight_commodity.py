from odoo import models, fields, api


class FreightCommodity(models.Model):
    _name = "freight.commodity"
    _description = "Commodity"
    _rec_name = 'display_name'

    display_name = fields.Char(compute='_compute_display_name', store=True)
    name = fields.Char(required=True)
    code = fields.Char(required=True)
    description = fields.Text()
    hs_code_id = fields.Many2one('harmonized.system.code', string="HS Code")
    hazardous = fields.Boolean(default=False, string="Is HAZ")

    _sql_constraints = [
        ('commodity_code_unique', 'UNIQUE(code)', "Code must be unique.")
    ]

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '[{}] {}'.format(rec.code, rec.name)
