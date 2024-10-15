from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FreightScheduleMixin(models.AbstractModel):
    _name = 'freight.schedule.mixin'
    _description = 'Freight Schedule Mixin'
    _order = 'actual_departure_date DESC,estimated_departure_date DESC'

    name = fields.Char(compute='_compute_name', store=True)
    carrier_id = fields.Many2one('freight.carrier', string='Carrier', required=True)
    vessel_id = fields.Many2one('freight.vessel')
    source = fields.Selection([('manual', 'Manual')], default='manual', readonly=True)
    transport_mode_id = fields.Many2one('transport.mode', required=True)
    transport_mode_type = fields.Selection(related='transport_mode_id.mode_type', store=True)

    # Location
    origin_port_id = fields.Many2one('freight.port', string='Origin Port', required=True)
    destination_port_id = fields.Many2one('freight.port', string='Destination Port', required=True)
    origin_country_id = fields.Many2one('res.country', string='Origin Country', related='origin_port_id.country_id', store=True)
    destination_country_id = fields.Many2one('res.country', string='Destination Country', related='destination_port_id.country_id', store=True)

    # Date and Time
    estimated_departure_date = fields.Datetime(string='ETD', help='Estimated Time Departure')
    actual_departure_date = fields.Datetime(string='ATD', help='Actual Time Departure')
    estimated_arrival_date = fields.Datetime(string='ETA', help='Estimated Time Arrival')
    actual_arrival_date = fields.Datetime(string='ATA', help='Actual Time Arrival')

    transit_time = fields.Integer('TT(In days)', compute='cal_transit_time', store=True, readonly=False)
    si_cutoff = fields.Datetime('SI Cut Off')

    @api.depends('carrier_id', 'origin_country_id', 'destination_country_id')
    def _compute_name(self):
        for rec in self:
            if rec.carrier_id and rec.origin_country_id and rec.destination_country_id:
                rec.name = '{} ({} → {})'.format(rec.carrier_id.name, rec.origin_country_id.code, rec.destination_country_id.code)
            else:
                rec.name = 'New Schedule'

    @api.constrains('estimated_arrival_date', 'estimated_departure_date')
    def _check_sailing_schedule_eta_etd(self):
        for rec in self:
            if rec.estimated_arrival_date and rec.estimated_departure_date and (rec.estimated_departure_date > rec.estimated_arrival_date):
                raise ValidationError(_(
                    'Estimated Departure date should be less than estimated arrival date.'))

    @api.constrains('actual_arrival_date', 'actual_departure_date')
    def _check_sailing_schedule_ata_atd(self):
        for rec in self:
            if rec.actual_arrival_date and rec.actual_departure_date and (rec.actual_departure_date > rec.actual_arrival_date):
                raise ValidationError(_(
                    'Actual Departure date should be less than actual arrival date.'))

    @api.constrains('origin_port_id', 'destination_port_id')
    def _check_sailing_schedule_port_unique(self):
        for rec in self:
            if rec.origin_port_id and rec.destination_port_id and \
                    rec.origin_port_id.id == rec.destination_port_id.id:
                raise ValidationError(_("Origin port and Destination port can't be same."))

    @api.depends('estimated_arrival_date', 'estimated_departure_date')
    def cal_transit_time(self):
        for rec in self:
            transit_time = 0
            if rec.estimated_departure_date and rec.estimated_arrival_date:
                transit_time = (rec.estimated_arrival_date - rec.estimated_departure_date).days
            rec.transit_time = transit_time
