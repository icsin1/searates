from odoo import models, fields


class FreightAirSchedule(models.Model):
    _name = 'freight.air.schedule'
    _inherit = 'freight.schedule.mixin'
    _description = 'Freight Air Schedule'

    origin_port_id = fields.Many2one('freight.port', string='Origin Airport', required=True, domain="[('transport_mode_type', '=', 'air')]")
    destination_port_id = fields.Many2one('freight.port', string='Destination AirPort', required=True, domain="[('transport_mode_type', '=', 'air')]")
    flight_number = fields.Char(string='Flight Number')
    icoa_number = fields.Char('Carrier ICOA Number', help='Carrier International Civil Aviation Organization')
    iata_number = fields.Char('Carrier IATA Number', help='Carrier International Air Transport Association')
