from odoo import models, _


class FreightAirSchedule(models.Model):
    _inherit = 'freight.air.schedule'

    def _on_air_schedule_selected(self, wizard, schedule):
        active_model = self.env.context.get('active_model')
        if active_model in ['freight.master.shipment', 'freight.house.shipment']:
            shipment = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id'))
            if shipment:
                # Note : In master shipment, the selection key of aircraft type is cao, so we need to make this fix later
                aircraft_type = schedule.aircraft_type
                if aircraft_type and aircraft_type == "coa":
                    aircraft_type = "cao"
                shipment_vals = {
                    'voyage_number': schedule.flight_number,
                    'shipping_line_id': schedule.carrier_id.id,
                    'etd_time': schedule.estimated_departure_date,
                    'eta_time': schedule.estimated_arrival_date,
                }
                if aircraft_type:
                    shipment_vals['aircraft_type'] = aircraft_type
                shipment.write(shipment_vals)
                self.notify_user(
                    _('Schedule Updated'),
                    _('{} Flight selected for shipment {}'.format(schedule.flight_number, shipment.name)),
                    'success'
                )
