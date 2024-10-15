from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SailingScheduleSelectorWizard(models.TransientModel):
    _name = 'sailing.schedule.selector.wizard'
    _description = 'Sailing Schedule Selector'

    origin_port_id = fields.Many2one('freight.port', string='Origin Port', required=True)
    destination_port_id = fields.Many2one('freight.port', string='Destination Port', required=True)
    transport_mode_id = fields.Many2one('transport.mode', default=lambda self: self.env.ref('freight_base.transport_mode_sea').id)
    carrier_id = fields.Many2one('freight.carrier')
    vessel_id = fields.Many2one('freight.vessel')
    departure_from_date = fields.Date()
    departure_to_date = fields.Date()
    arrival_from_date = fields.Date()
    arrival_to_date = fields.Date()
    schedule_ids = fields.Many2many('freight.schedule')

    def _generate_domain(self):
        self.ensure_one()
        domain = []
        if not self.origin_port_id and not self.destination_port_id:
            return []
        domain += [('origin_port_id', '=', self.origin_port_id.id)]
        domain += [('destination_port_id', '=', self.destination_port_id.id)]
        if self.carrier_id:
            domain += [('carrier_id', '=', self.carrier_id.id)]
        if self.vessel_id:
            domain += [('vessel_id', '=', self.vessel_id.id)]
        if self.departure_from_date:
            departure_domain = [('estimated_departure_date', '>=', self.departure_from_date)]
            if self.departure_to_date:
                departure_domain += [('estimated_departure_date', '<=', self.departure_to_date)]
            domain += departure_domain
        if self.arrival_from_date:
            arrival_domain = [('estimated_arrival_date', '>=', self.arrival_from_date)]
            if self.arrival_to_date:
                arrival_domain += [('estimated_arrival_date', '<=', self.arrival_to_date)]
            domain += arrival_domain
        if self.transport_mode_id:
            domain += [('transport_mode_id', '=', self.transport_mode_id.id)]
        return domain

    @api.onchange('origin_port_id', 'destination_port_id', 'carrier_id', 'vessel_id', 'departure_from_date',
                  'departure_to_date', 'arrival_from_date', 'arrival_to_date')
    def _onchange_fields(self):
        records = self.env['freight.schedule'].sudo().search(self._generate_domain())
        self.schedule_ids = [(6, False, records.ids)]

    @api.constrains('departure_from_date', 'departure_to_date', 'arrival_from_date', 'arrival_to_date')
    def _check_eta_etd_ata_atd_date(self):
        date_field = ['departure_from_date', 'departure_to_date', 'arrival_from_date', 'arrival_to_date']
        # Validation for dates - date in sequence should be earlier than it's next date
        # Departure From Date < Departure To Date < Arrival From Date < Arrival To Date
        for rec in self:
            dates = {df: rec[df] for df in date_field if rec[df]}
            keys_list = list(dates)
            for current_field, next_field in zip(keys_list, keys_list[1:]):
                if dates[current_field] > dates[next_field]:
                    raise ValidationError(_('%s: %s is earlier than %s: %s.') % (
                        next_field.replace('_', ' ').title(), dates[next_field], current_field.replace('_', ' ').title(), dates[current_field]))

    @api.constrains('origin_port_id', 'destination_port_id')
    def _check_port_unique(self):
        for rec in self:
            if rec.origin_port_id.id == rec.destination_port_id.id:
                raise ValidationError(_("Origin port and Destination port can't be same."))
