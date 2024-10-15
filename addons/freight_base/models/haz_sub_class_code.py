from odoo import fields, models


class HazardousSubstancesClassCode(models.Model):
    _name = 'haz.sub.class.code'
    _description = 'Hazardous Substances Class Code'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    description = fields.Text()
