from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FreightSchedule(models.Model):
    _name = 'freight.schedule'
    _inherit = 'freight.schedule.mixin'
    _description = 'Freight Schedule'

    origin_port_id = fields.Many2one('freight.port', string='Origin Port', required=True, domain="[('transport_mode_type', '=', 'sea')]")
    destination_port_id = fields.Many2one('freight.port', string='Destination Port', required=True, domain="[('transport_mode_type', '=', 'sea')]")
    vessel_id = fields.Many2one('freight.vessel', domain="[('carrier_id', '=', carrier_id)]")

    @api.constrains('estimated_departure_date', 'vessel_cut_off')
    def _check_sailing_schedule_etd_vessel_cut_off(self):
        for rec in self:
            if rec.estimated_departure_date and rec.vessel_cut_off and (rec.vessel_cut_off > rec.estimated_departure_date):
                raise ValidationError(_(
                    'The vessel cut off date should not be greater than ETD date.'))
