import logging
import requests
from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT


_logger = logging.getLogger(__name__)


class OAGScheduleSearchWizard(models.TransientModel):
    _name = 'oag.schedule.search.wizard'
    _description = 'OAG Schedule Search'

    transport_mode_id = fields.Many2one('transport.mode', required=True)
    source = fields.Char(required=True, default='oag')
    origin_port_id = fields.Many2one('freight.port', string='Origin Airport', required=True, domain="[('transport_mode_id', '=', transport_mode_id)]")
    destination_port_id = fields.Many2one('freight.port', string='Destination Airport', required=True, domain="[('transport_mode_id', '=', transport_mode_id)]")
    search_date_mode = fields.Selection([
        ('departure', 'By Departure Date'),
        ('arrival', 'By Arrival Date')
    ], default='departure', required=True)
    date = fields.Date(string='Date', required=True)
    aircraft_type = fields.Selection([
        ('coa', 'Cargo'),
        ('pax', 'Passenger')
    ], copy=False, string="Aircraft Type", default='coa')
    import_all_schedule = fields.Boolean(default=False)
    schedule_ids = fields.One2many('oag.schedule.result', 'wizard_id')

    @api.onchange('import_all_schedule')
    def _onchange_import_all_schedule(self):
        for rec in self:
            rec.schedule_ids.import_schedule = rec.import_all_schedule

    def action_import_schedules(self):
        selected_schedules = self.schedule_ids.filtered(lambda s: s.import_schedule)
        if not selected_schedules:
            raise UserError(_("No Schedule Selected for Import."))
        if selected_schedules:
            FreightSchedule = self.env['freight.air.schedule'].sudo()
            values_list = []
            for schedule in selected_schedules:
                carrier = schedule._find_carrier()
                existing = FreightSchedule.search([
                    ('carrier_id', '=', carrier.id),
                    ('flight_number', '=', schedule.flight_number),
                    ('origin_port_id', '=', self.origin_port_id.id),
                    ('destination_port_id', '=', self.destination_port_id.id),
                    ('estimated_departure_date', '=', schedule.departure_datetime),
                    ('estimated_arrival_date', '=', schedule.arrival_datetime),
                    ('aircraft_type', '=', schedule.aircraft_type)
                ])
                if not existing:
                    values_list.append({
                        'transport_mode_id': self.transport_mode_id.id,
                        'source': self.source,
                        'origin_port_id': self.origin_port_id.id,
                        'destination_port_id': self.destination_port_id.id,
                        'carrier_id': carrier.id,
                        'estimated_departure_date': schedule.departure_datetime,
                        'estimated_arrival_date': schedule.arrival_datetime,
                        'actual_departure_date': schedule.departure_datetime,
                        'actual_arrival_date': schedule.arrival_datetime,
                        'flight_number': schedule.flight_number,
                        'iata_number': schedule.iata_code,
                        'flight_status': schedule.flight_status,
                        'aircraft_type': schedule.aircraft_type,
                    })
            if values_list:
                FreightSchedule.create(values_list)
            self.notify_user(_('Schedule Imported'), _('{} Air Schedule Imported'.format(len(selected_schedules))), 'success')
        if self.env.context.get('open_selector_wizard'):
            return {
                'name': _('Find Airline from Schedule'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'air.schedule.selector.wizard',
                'res_id': self.env.context.get('open_selector_wizard'),
                'views': [(False, 'form')],
                'view_id': False,
                'target': 'new',
                'context': self.env.context.get('selector_wizard_context', {}),
            }
        return {'type': 'ir.actions.act_window_close'}

    def _get_oag_configs(self):
        ICP = self.env['ir.config_parameter'].sudo()

        is_sandbox = ICP.get_param('fm_oag_air_schedule.oag_environment', 'sandbox') == 'sandbox'

        return {
            'api_key': ICP.get_param('fm_oag_air_schedule.oag_api_key'),
            'is_sandbox': is_sandbox,
            'base_url':  'https://api.oag.com/'
        }

    def _search_schedules(self, origin_port, destination_port, date_mode, date, aircraft_type):
        configs = self._get_oag_configs()
        url = "{}/flight-instances".format(configs.get('base_url'))
        headers = {'Subscription-Key': configs.get('api_key')}
        params = {
            'version': 'v2',
            'DepartureAirport': origin_port,
            'ArrivalAirport': destination_port,
            'CodeType': 'IATA',
            'ServiceType': aircraft_type and aircraft_type == "coa" and 'Cargo' or aircraft_type == "pax" and 'Passenger' or 'Cargo',
            'DepartureDateTime' if date_mode == 'departure' else 'ArrivalDateTime': date
        }
        response = requests.get(url, params=params, headers=headers)
        result = response.json()
        if response.status_code not in [200] or not isinstance(result.get('data'), list):
            error_msg = ''
            if result.get('title', False) and isinstance(result.get('title'), str):
                error_msg = result.get('title')
            elif result.get('message', False) and isinstance(result.get('message'), str):
                error_msg = result.get('message')
            if not error_msg:
                error_msg = "Some issue while fetching Air schedules."
            raise UserError(_(error_msg))
        return result.get('data', [])

    def _find_carrier(self, iata):
        airline = self.env['freight.carrier'].sudo().search([
            ('iata_code', '!=', False), ('iata_code', '=', iata), ('transport_mode_id.mode_type', '=', 'air')
        ], limit=1)
        return airline

    def _convert_to_lines(self, schedules):
        """
            While fetching the schedules from oag, if the carrier with proper IATA code will not be found in our erp
            we are going to ignore such records.So,such schedules will not be imported in our erp.
        """
        lines = []
        missing_carrier_iata = []
        for schedule in schedules:
            carrier = schedule.get("carrier")
            carrier_iata = carrier and carrier.get('iata', '') or ''
            # Currently, we are only considering the carriers with IATA number
            if not carrier_iata:
                continue
            carrier_id = self._find_carrier(carrier_iata)
            if not carrier_id:
                missing_carrier_iata.append(carrier_iata)
                continue
            departure = schedule.get("departure")
            arrival = schedule.get("arrival")
            departure_datetime = False
            arrival_datetime = False
            departure_date = departure.get('date').get('utc', departure.get('date').get('local'))
            departure_time = departure.get('time').get('utc', departure.get('time').get('local', '00:00:00'))
            arrival_date = arrival.get('date').get('utc', departure.get('date').get('local'))
            arrival_time = arrival.get('time').get('utc', departure.get('time').get('local', '00:00:00'))
            if departure_date:
                departure_datetime = "{} {}".format(departure_date, departure_time)
            if arrival_date:
                arrival_datetime = "{} {}".format(arrival_date, arrival_time)
            lines.append(Command.create({
                'flight_number': schedule.get('flightNumber'),
                'flight_status': schedule.get('flightType'),
                'departure_datetime': departure_datetime,
                'arrival_datetime': arrival_datetime,
                'origin_terminal': arrival.get('terminal', ''),
                'destination_terminal': departure.get('terminal', ''),
                'import_schedule': self.import_all_schedule,
                'iata_code': carrier_iata,
                'aircraft_type': self.aircraft_type,
            }))
        if not lines and missing_carrier_iata:
            raise UserError(_("Airline with IATA code %s not found. Please make sure that the airline is available in system and it has proper IATA code." % ', '.join(missing_carrier_iata)))
        return lines

    @api.onchange('origin_port_id', 'destination_port_id', 'search_date_mode', 'date', 'aircraft_type')
    def _onchange_of_values(self):
        self.write({'schedule_ids': False})

    def action_search_air_schedules(self):
        self.write({'schedule_ids': False})
        if self.origin_port_id and self.destination_port_id and self.search_date_mode and self.date:
            schedules = self._search_schedules(
                self.origin_port_id.code,
                self.destination_port_id.code,
                self.search_date_mode,
                self.date.strftime(DATE_FORMAT),
                self.aircraft_type,
            )
            if not schedules:
                raise UserError(_("No Schedule record found."))

            self.write({'schedule_ids': self._convert_to_lines(schedules)})

        return {
            'name': _('Import Air Schedule'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'oag.schedule.search.wizard',
            'res_id': self.id,
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
        }


class OAGScheduleResult(models.TransientModel):
    _name = 'oag.schedule.result'
    _description = 'OAG Schedule Result'
    _order = 'departure_datetime'

    wizard_id = fields.Many2one('oag.schedule.search.wizard', ondelete='cascade', required=True)
    import_schedule = fields.Boolean(default=False)
    origin_terminal = fields.Char(string='Origin Terminal')
    destination_terminal = fields.Char(string='Destination Terminal')
    departure_datetime = fields.Datetime('Departure Time')
    arrival_datetime = fields.Datetime('Arrival Time')
    total_duration = fields.Integer(string='Total Duration')
    terminal_cutoff = fields.Datetime(string='Terminal CutOff')
    flight_status = fields.Char('Flight Status')
    flight_number = fields.Char('Flight Number')
    iata_code = fields.Char("IATA Code")
    aircraft_type = fields.Selection([
        ('coa', 'Cargo'),
        ('pax', 'Passenger')
    ], string="Service Type")

    def _find_carrier(self):
        self.ensure_one()
        carrier_obj = self.env['freight.carrier'].sudo().search([('iata_code', '!=', False), ('iata_code', '=', self.iata_code)], limit=1)
        if not carrier_obj:
            raise UserError(_("Airline with IATA code %s not found. Please make sure that the airline is available in system and it has proper IATA code." % self.iata_code))
        return carrier_obj
