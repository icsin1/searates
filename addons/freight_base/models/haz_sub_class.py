from odoo import fields, models


class HazardousSubClass(models.Model):
    _name = 'haz.sub.class'
    _description = 'Hazardous Substances Class'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    haz_class_id = fields.Many2one('haz.sub.class.code', string='HAZ Class', required=True)
