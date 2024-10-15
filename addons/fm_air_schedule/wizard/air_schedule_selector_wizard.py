from odoo import models, fields, api
import json


class AirScheduleSelectorWizard(models.TransientModel):
    _name = 'air.schedule.selector.wizard'
    _description = 'Air Schedule Selector'

    @api.depends('transport_mode_id')
    def _compute_carrier_domain(self):
        for rec in self:
            domain = [('transport_mode_id', '=', rec.transport_mode_id.id)]
            rec.carrier_domain = json.dumps(domain)

    carrier_domain = fields.Char(compute='_compute_carrier_domain', store=True)

    origin_port_id = fields.Many2one('freight.port', string='Origin Airport', required=True, domain="[('transport_mode_type', '=', 'air')]")
    destination_port_id = fields.Many2one('freight.port', string='Destination Airport', required=True, domain="[('transport_mode_type', '=', 'air')]")
    transport_mode_id = fields.Many2one('transport.mode', default=lambda self: self.env.ref('freight_base.transport_mode_air').id)
    carrier_id = fields.Many2one('freight.carrier', string="Airline")
    departure_date = fields.Date()
    arrival_date = fields.Date()
    flight_number = fields.Char()
    schedule_ids = fields.Many2many('freight.air.schedule')

    def _generate_domain(self):
        self.ensure_one()
        domain = []
        if not self.origin_port_id and not self.destination_port_id:
            return
        domain += [('origin_port_id', '=', self.origin_port_id.id)]
        domain += [('destination_port_id', '=', self.destination_port_id.id)]
        if self.carrier_id:
            domain += [('carrier_id', '=', self.carrier_id.id)]
        if self.flight_number:
            domain += [('flight_number', '=', self.flight_number)]
        if self.departure_date:
            departure_domain = [('estimated_departure_date', '>=', self.departure_date)]
            domain += departure_domain
        if self.arrival_date:
            arrival_domain = [('estimated_arrival_date', '>=', self.arrival_date)]
            domain += arrival_domain
        if self.transport_mode_id:
            domain += [('transport_mode_id', '=', self.transport_mode_id.id)]
        return domain

    @api.onchange('origin_port_id', 'destination_port_id', 'carrier_id', 'departure_date', 'arrival_date', 'flight_number')
    def _onchange_fields(self):
        if self._generate_domain():
            records = self.env['freight.air.schedule'].sudo().search(self._generate_domain())
            self.schedule_ids = [(6, False, records.ids)]
