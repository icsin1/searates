from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FreightDepartureArrivalMixin(models.AbstractModel):
    _name = 'freight.departure.arrival.mixin'
    _description = 'Freight Departure-Arrival time Mixin'

    # Arrival and Departures
    etd_time = fields.Datetime(string='ETD', help='Estimated Time Departure')
    eta_time = fields.Datetime(string='ETA', help='Estimated Time Arrival')
    atd_time = fields.Datetime(string='ATD', help='Actual Time Departure')
    ata_time = fields.Datetime(string='ATA', help='Actual Time Arrival')

    @api.constrains('eta_time', 'etd_time')
    def _check_record_eta_etd_time(self):
        for record in self:
            if record.eta_time and record.etd_time and (record.etd_time > record.eta_time):
                raise ValidationError(_(
                    'Estimated Departure date should be less than estimated arrival date.'))

    @api.constrains('ata_time', 'atd_time')
    def _check_record_ata_atd_time(self):
        for record in self:
            if record.ata_time and record.atd_time and (record.atd_time > record.ata_time):
                raise ValidationError(_(
                    'Actual Departure date should be less than actual arrival date.'))
