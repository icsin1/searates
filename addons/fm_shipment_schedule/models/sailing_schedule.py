from odoo import models, _


class FreightSailingSchedule(models.Model):
    _inherit = 'freight.schedule'

    def _on_sailing_schedule_selected(self, wizard, schedule):
        if self.env.context.get('active_model') in ('freight.master.shipment', 'freight.house.shipment'):
            shipment = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id'))
            if shipment:
                shipment.write({
                    'voyage_number': schedule.voyage_number,
                    'shipping_line_id': schedule.carrier_id.id,
                    'vessel_id': schedule.vessel_id.id,
                    'carrier_vessel_cut_off_datetime': schedule.vessel_cut_off,
                    'carrier_vgm_cut_off_datetime': schedule.vgm_cut_off,
                    'etd_time': schedule.estimated_departure_date,
                    'eta_time': schedule.estimated_arrival_date
                })
                self.notify_user(
                    _('Schedule Updated'),
                    _('{} Voyage selected for shipment {}'.format(schedule.voyage_number, shipment.name)),
                    'success'
                )
