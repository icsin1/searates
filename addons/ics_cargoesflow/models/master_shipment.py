import traceback
import logging
from datetime import datetime
from odoo import models, fields, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from .cargoesflow_api import CargoesflowAPI

_logger = logging.getLogger(__name__)


class FreightMasterShipment(models.Model):
    _inherit = 'freight.master.shipment'

    synced_with_cargoflow = fields.Boolean("Synced Shipment")
    shipment_tracking_url = fields.Char('Shipment tracking URL')
    submit_cargoflow_shipment = fields.Boolean(string='Submitted for CargoesFlow')

    def write(self, values):
        res = super().write(values)
        records_to_sync = self.filtered(lambda record: record.state == 'booked' and record.mode_type in ['sea', 'air'] and record.house_shipment_ids and record.carrier_booking_reference_number)
        if records_to_sync:
            self.env.ref('ics_cargoesflow.ir_cron_sync_cargoesflow_shipments')._trigger()
        return res

    def action_submit_cargoflow_shipment(self):
        if self.house_shipment_count < 1:
            raise ValidationError(_("Please attach at least one house shipment."))
        self.write({
                'submit_cargoflow_shipment': True
            })
        self.action_sync_cargoflow_shipment()

    def action_sync_cargoflow_shipment(self):
        self.with_context(shipments_to_sync=self.ids)._cron_sync_cargoesflow_shipments()

    def action_update_milestones_for_shipment(self):
        self.with_context(shipments_to_sync=self.ids)._cron_sync_cargoesflow_shipment_milestones()

    def _cron_sync_cargoesflow_shipments(self):
        """ Cron job which will be triggered when any new shipment need to sync at the time of write and based on 4 hr interval """
        domain = [
            ('synced_with_cargoflow', '=', False),
            ('mode_type', 'in', ['sea', 'air']),
            ('house_shipment_ids', '!=', False),
            ('carrier_booking_reference_number', '!=', False),
            '|',
                ('carrier_booking_container_ids', '!=', False),
                ('submit_cargoflow_shipment','=',True),
            '|',
                ('state', '=', 'booked'),
                ('submit_cargoflow_shipment','=',True)
        ]
        shipment_ids = self.env.context.get("shipments_to_sync", [])

        if shipment_ids:
            domain += [('id', 'in', shipment_ids)]

        shipments_to_create = self.sudo().search(domain)
        if shipments_to_create:
            _logger.info("Syncing Cargoes Flow for shipments {}".format(','.join(shipments_to_create.mapped('display_name'))))
            shipments_to_create._sync_cargoflow_shipment()

    def _sync_cargoflow_shipment(self):

        sea_form_data = {}
        air_form_data = {}

        shipments = self.filtered(lambda shipment: shipment.house_shipment_ids and (shipment.state == 'booked' or shipment.state == 'draft') and not shipment.synced_with_cargoflow)

        # Grouping Shipment Payloads for Sea and Air
        for shipment in shipments:
            # FIXME
            # Currently removing additional hyphen from 'carrier_booking_reference_number' to match the number in Air Cargoes flow
            # 'carrier_booking_reference_number' is coming from ERP system be like 160-12345678 but actual number will be 16012345678
            carrier_booking_reference_number = shipment.carrier_booking_reference_number.replace('-','')
            if shipment.mode_type == 'sea':
                sea_form_data.update({
                    shipment: {
                        "oceanLine": shipment.shipping_line_id and shipment.shipping_line_id.name or "",
                        "mblNumber": carrier_booking_reference_number or "",
                        "bookingNumber": shipment.name or "",
                        "promisedEta": shipment.eta_time.strftime(DEFAULT_SERVER_DATE_FORMAT) if shipment.eta_time else ''
                    }
                })
            else:
                air_form_data.update({
                    shipment: {
                        "awbNumber": carrier_booking_reference_number or "",
                    }
                })

        cargoesflow_api = CargoesflowAPI(self.env)

        # Creating Sea Shipments
        if sea_form_data:
            try:
                cargoesflow_api._create_shipment({
                    'formData': list(sea_form_data.values()),
                    'uploadType': 'FORM_BY_MBL_NUMBER'
                })
            except Exception:
                traceback.print_exc()

        # Creating Air Shipments
        if air_form_data:
            try:
                cargoesflow_api._create_shipment({
                    'formData': list(air_form_data.values()),
                    'uploadType': 'FORM_BY_AWB_NUMBER'
                })
            except Exception:
                traceback.print_exc()

        # Updating Tracking URLs
        for shipment in shipments:
            _logger.info("Cargosflow Shipment Sync: {}".format(shipment.display_name))
            try:
                # FIXME
                # Currently removing additional hyphen from 'carrier_booking_reference_number' to match the number in Air Cargoes flow
                # 'carrier_booking_reference_number' is coming from ERP system be like 160-12345678 but actual number will be 16012345678
                carrier_booking_reference_number = shipment.carrier_booking_reference_number.replace('-','')
                tracking_url = cargoesflow_api._get_shipment_tracking_url(carrier_booking_reference_number, mode_type=shipment.mode_type)
                shipment.write({
                    'synced_with_cargoflow': True,
                    'shipment_tracking_url': tracking_url
                })
                if tracking_url:
                    shipment.message_post(body='Shipment Synced with CargoesFlow with Tracking URL {}'.format(tracking_url))
            except Exception as e:
                shipment.message_post(body='ERROR: {}'.format(str(e)))
                traceback.print_exc()

    def _cron_sync_cargoesflow_shipment_milestones(self):
        domain = [
            ('mode_type', 'in', ('sea', 'air')),
            '|',
                ('state', 'not in', ('draft', 'cancelled', 'completed')),
                ('submit_cargoflow_shipment', '=', True),
            ('synced_with_cargoflow', '=', True)
        ]
        shipment_ids = self.env.context.get("shipments_to_sync", [])

        if shipment_ids:
            domain += [('id', 'in', shipment_ids)]

        shipments = self.sudo().search(domain)

        _logger.info("Syncing Cargoes Flow for shipments' milestones {}".format(','.join(shipments.mapped('display_name'))))

        cargoesflow_api = CargoesflowAPI(self.env)
        for shipment in shipments:
            _logger.info("Cargosflow Shipment Milestone Sync: {}".format(shipment.display_name))
            # FIXME
            # Currently removing additional hyphen from 'carrier_booking_reference_number' to match the number in Air Cargoes flow
            # 'carrier_booking_reference_number' is coming from ERP system be like 160-12345678 but actual number will be 16012345678
            carrier_booking_reference_number = shipment.carrier_booking_reference_number.replace('-','')
            detail_list = cargoesflow_api._get_shipment_detail(carrier_booking_reference_number, shipment_type='INTERMODAL_SHIPMENT' if shipment.mode_type == 'sea' else 'AIR_SHIPMENT')
            events = []
            for details in detail_list:
                events += shipment._update_cargoesflow_shipment_events(details.get('shipmentNumber'), details.get('containerNumber', None), details.get('shipmentEvents', []))
                # shipment.message_post(body=_("Current Shipment Status: {}".format(details.get('status'))))
            if events:
                shipment.event_ids.filtered(lambda event: event.cargoes_flow_event).unlink()
                shipment.event_ids = events
                for house_shipment in shipment.house_shipment_ids:
                    house_shipment.event_ids.filtered(lambda event: event.cargoes_flow_event).unlink()
                    house_shipment.event_ids = events

    def _update_cargoesflow_shipment_events(self, shipment_number, container_number, cargoesflow_events):
        self.ensure_one()
        EventType = self.env['freight.event.type'].sudo()
        events = []
        for shipment_event in cargoesflow_events:
            if shipment_event.get('code'):
                event_type = EventType.search([('code', '=', shipment_event.get('code'))], limit=1)
                if not event_type:
                    event_type = EventType.create({
                        'name': shipment_event.get('name'),
                        'code': shipment_event.get('code'),
                        'description': shipment_event.get('name')
                    })

                est_date = False
                act_date = False
                if shipment_event.get('estimateTime', False):
                    est_date = datetime.strptime(shipment_event['estimateTime'], "%Y-%m-%d %H:%M:%S %p")
                if shipment_event.get('actualTime', False):
                    act_date = datetime.strptime(shipment_event['actualTime'], "%Y-%m-%d %H:%M:%S %p")

                package_lists = self.container_ids if self.packaging_mode == 'container' else self.package_ids
                house_packages_ids = self.env['freight.master.shipment.container.number']
                if self.mode_type == 'sea':
                    house_packages_ids = package_lists.filtered(lambda pack: pack.container_number.container_number == container_number)
                if house_packages_ids or self.mode_type == 'air':
                    values = {
                        'cargoes_flow_shipment_number': shipment_number,
                        'event_type_id': event_type.id,
                        'cargoes_flow_event': True,
                        'public_visible': True,
                        'description': shipment_event.get('name', ''),
                        'location': shipment_event.get('location', ''),
                        'estimated_datetime': est_date,
                        'actual_datetime': act_date,
                    }
                    if house_packages_ids:
                        values.update({
                                'container_id': house_packages_ids and house_packages_ids[0].container_number.id,
                            })
                    events.append((0, 0, values))
        return events

    def action_track_air_shipment(self):
        tracking_url = self.shipment_tracking_url
        if tracking_url:
            return {
                'type': 'ir.actions.act_url',
                'url': tracking_url,
                'target': 'new',
            }
        return {}
