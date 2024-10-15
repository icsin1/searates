from odoo import models, fields, api


class FreightAirSchedule(models.Model):
    _inherit = 'freight.air.schedule'

    aircraft_type = fields.Selection([
        ('coa', 'COA'),
        ('pax', 'PAX')
    ], copy=False, string="Aircraft Type")
    service_name = fields.Char('Service Name')
