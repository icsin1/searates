import logging
import requests
from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT


_logger = logging.getLogger(__name__)


class INTTRAScheduleSearchWizard(models.TransientModel):
    _name = 'inttra.schedule.search.wizard'
    _description = 'INTTRA Schedule Search'

    transport_mode_id = fields.Many2one('transport.mode', required=True)
    source = fields.Char(required=True, default='inttra')
    origin_port_id = fields.Many2one('freight.port', string='Origin Port', required=True)
    destination_port_id = fields.Many2one('freight.port', string='Destination Port', required=True)
    search_date_mode = fields.Selection([
        ('departure', 'By Departure Date'),
        ('arrival', 'By Arrival Date')
    ], default='departure', required=True)
    weekout_number = fields.Selection([(str(i), str(i)) for i in range(1, 7, 1)], default='6', required=True)
    shipment_date = fields.Date(string='Shipment Date', required=True)

    import_all_schedule = fields.Boolean(default=False)
    # API Tokens
    inttra_session_token = fields.Char()
    schedule_ids = fields.One2many('inttra.schedule.result', 'wizard_id')

    @api.onchange('import_all_schedule')
    def _onchange_import_all_schedule(self):
        for rec in self:
            rec.schedule_ids.import_schedule = rec.import_all_schedule

    def action_import_schedules(self):
        FreightSchedule = self.env['freight.schedule'].sudo()
        selected_schedules = self.schedule_ids.filtered(lambda s: s.import_schedule)
        if not selected_schedules:
            raise UserError(_("No Schedule Selected for Import."))

        if selected_schedules:
            FreightSchedule = self.create_freight_schedule(selected_schedules)
            self.notify_user(_('Schedule Imported'), _('{} Sailing Schedule Imported'.format(len(FreightSchedule))), 'success')

        if self.env.context.get('open_selector_wizard'):
            return {
                'name': _('Find Voyage from Schedule'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'sailing.schedule.selector.wizard',
                'res_id': self.env.context.get('open_selector_wizard'),
                'views': [(False, 'form')],
                'view_id': False,
                'target': 'new',
                'context': self.env.context.get('selector_wizard_context', {}),
            }
        return FreightSchedule

    def _get_inttra_configs(self):
        ICP = self.env['ir.config_parameter'].sudo()

        is_sandbox = ICP.get_param('fm_inttra_sailing_schedule.inttra_environment', 'sandbox') == 'sandbox'

        return {
            'client_id': ICP.get_param('fm_inttra_sailing_schedule.inttra_client_id'),
            'client_secret': ICP.get_param('fm_inttra_sailing_schedule.inttra_client_secret'),
            'grant_type': ICP.get_param('fm_inttra_sailing_schedule.inttra_grant_type'),
            'is_sandbox': is_sandbox,
            'base_url': 'https://api-test.inttra.com' if is_sandbox else 'https://api.inttra.com'
        }

    def _get_session_token(self):
        _logger.info("Getting Session token from INTTRA")
        configs = self._get_inttra_configs()
        url = "{}/auth".format(configs.get('base_url'))
        headers = {
            'client_id': configs.get('client_id'),
            'client_secret': configs.get('client_secret'),
            'grant_type': configs.get("grant_type")
        }
        response = requests.get(url, headers=headers)
        result = response.json()
        if response.status_code not in [200] or 'access_token' not in result:
            raise UserError(_('\n'.join(result.get('errorMessages', []))))
        # Returning access token
        return result.get('access_token')

    def _search_schedules(self, token, origin_port, destination_port, date_mode, weekout, shipment_date):
        _logger.info("Getting Session token from INTTRA")
        configs = self._get_inttra_configs()
        url = "{}/oceanschedules/schedule".format(configs.get('base_url'))
        headers = {'Authorization': token}
        params = {
            'searchDate': shipment_date,
            'searchDateType': date_mode,
            'originPort': origin_port,
            'destinationPort': destination_port,
            'weeksOut': weekout
        }
        response = requests.get(url, params=params, headers=headers)
        result = response.json()
        if response.status_code not in [200] or not isinstance(result, list):
            raise UserError(_('\n'.join(result.get('errorMessages', []))))
        return result

    def _convert_to_lines(self, schedules):
        lines = []
        for schedule in schedules:
            lines.append(Command.create({
                'scac': schedule.get('scac'),
                'carrier_name': schedule.get('carrierName'),
                'service_name': schedule.get('serviceName'),
                'vessel_name': schedule.get('vesselName'),
                'voyage_number': schedule.get('voyageNumber'),
                'imo_number': schedule.get('imoNumber'),
                'origin_terminal': schedule.get('originTerminal'),
                'destination_terminal': schedule.get('destinationTerminal'),
                'departure_datetime': schedule.get('originDepartureDate'),
                'arrival_datetime': schedule.get('destinationArrivalDate'),
                'terminal_cutoff': schedule.get('terminalCutoff'),
                'vgm_cutoff': schedule.get('vgmCutoff'),
                'total_duration': schedule.get('totalDuration'),
                'import_schedule': self.import_all_schedule
            }))
        return lines

    @api.onchange('origin_port_id', 'destination_port_id', 'search_date_mode', 'weekout_number', 'shipment_date')
    def _onchange_of_values(self):
        self.update({'schedule_ids': False})

    def action_search_sailing_schedules(self):
        self.write({'schedule_ids': False})
        if not self.inttra_session_token:
            self.write({'inttra_session_token': self._get_session_token()})

        schedules = self._search_schedules(
            self.inttra_session_token,
            self.origin_port_id.code,
            self.destination_port_id.code,
            'ByDepartureDate' if self.search_date_mode == 'departure' else 'ByArrivalDate',
            self.weekout_number,
            self.shipment_date.strftime(DATE_FORMAT)
        )
        self.write({'schedule_ids': self._convert_to_lines(schedules)})
        if not self.schedule_ids:
            raise UserError(_("No Schedule record found."))

        return {
            'name': _('Import Sailing Schedule'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'inttra.schedule.search.wizard',
            'res_id': self.id,
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
        }

    def create_freight_schedule(self, selected_schedules):
        FreightSchedule = self.env['freight.schedule'].sudo()
        values_list = []
        existing_record_ids = self.env['freight.schedule']
        for schedule in selected_schedules:
            carrier = schedule._get_or_create_carrier()
            vessel = schedule._get_or_create_vessel()
            existing = FreightSchedule.search([
                ('carrier_id', '=', carrier.id),
                ('vessel_id', '=', vessel.id),
                ('voyage_number', '=', schedule.voyage_number),
                ('origin_port_id', '=', self.origin_port_id.id),
                ('destination_port_id', '=', self.destination_port_id.id),
                ('estimated_departure_date', '=', schedule.departure_datetime),
                ('estimated_arrival_date', '=', schedule.arrival_datetime)
            ])
            if not existing:
                values_list.append({
                    'transport_mode_id': self.transport_mode_id.id,
                    'source': self.source,
                    'origin_port_id': self.origin_port_id.id,
                    'destination_port_id': self.destination_port_id.id,
                    'carrier_id': carrier.id,
                    'voyage_number': schedule.voyage_number,
                    'imo_number': schedule.imo_number,
                    'scac_number': schedule.scac,
                    'service_name': schedule.service_name,
                    'estimated_departure_date': schedule.departure_datetime,
                    'estimated_arrival_date': schedule.arrival_datetime,
                    'vessel_cut_off': schedule.terminal_cutoff,
                    'vgm_cut_off': schedule.vgm_cutoff,
                    'vessel_id': vessel.id
                })
            else:
                existing_record_ids |= existing
        return FreightSchedule.create(values_list) + existing_record_ids


class INTTRAScheduleResult(models.TransientModel):
    """
    {
            "scac": "MSCU",
            "carrierName": "MSC",
            "serviceName": "INDUS EXPRESS",
            "vesselName": "MSC RANIA",
            "voyageNumber": "IU324A",
            "imoNumber": "9309447",
            "originTerminal": "JEBEL ALI CONTAINER TERMINAL 1",
            "destinationTerminal": "ADANI INTERNATIONAL CONTAINER TERMINAL PVT LTD",
            "originDepartureDate": "2023-06-19 03:30:00",
            "destinationArrivalDate": "2023-06-26 12:00:00",
            "estimatedTerminalCutoff": null,
            "terminalCutoff": "2023-06-14 10:00:00",
            "vgmCutoff": "2023-06-15 00:00:00",
            "totalDuration": 8,
            "legs": null
        }
    """
    _name = 'inttra.schedule.result'
    _description = 'INTTRA Schedule Result'
    _order = 'departure_datetime'

    wizard_id = fields.Many2one('inttra.schedule.search.wizard', ondelete='cascade', required=True)
    import_schedule = fields.Boolean(default=False)
    scac = fields.Char(string='SCAC Code')
    carrier_name = fields.Char(string='Carrier Name')
    service_name = fields.Char(string='Service Name')
    vessel_name = fields.Char(string='Vessel Name')
    voyage_number = fields.Char(string='Voyage Number')
    imo_number = fields.Char(string='IMO Number')
    origin_terminal = fields.Char(string='Origin Terminal')
    destination_terminal = fields.Char(string='Destination Terminal')
    departure_datetime = fields.Datetime('Departure Time')
    arrival_datetime = fields.Datetime('Arrival Time')
    total_duration = fields.Integer(string='Total Duration')
    terminal_cutoff = fields.Datetime(string='Terminal CutOff')
    vgm_cutoff = fields.Datetime(string='VGM CutOff')

    def _get_or_create_carrier(self):
        self.ensure_one()
        Carrier = self.env['freight.carrier'].sudo()
        carrier_obj = Carrier.search([('scac_code', '!=', False), ('scac_code', '=', self.scac)], limit=1)
        if not carrier_obj:
            carrier_obj = Carrier.create({
                'name': self.carrier_name,
                'is_sea_carrier': True,
                'scac_code': self.scac,
                'transport_mode_id': self.wizard_id.transport_mode_id.id
            })
        return carrier_obj

    def _get_or_create_vessel(self):
        self.ensure_one()
        Vessel = self.env['freight.vessel'].sudo()
        vessel_obj = Vessel.search([('imo_number', '!=', False), ('imo_number', '=', self.imo_number)], limit=1)
        if not vessel_obj:
            vessel_obj = Vessel.create({
                'name': self.vessel_name,
                'code': self.vessel_name,
                'imo_number': self.imo_number,
                'carrier_id': self._get_or_create_carrier().id,
            })
        return vessel_obj
