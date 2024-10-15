from odoo import models, _


class FreightMasterShipment(models.Model):
    _inherit = 'freight.master.shipment'

    def action_fetch_flight_number(self):
        self.ensure_one()
        ctx = {
            'default_origin_port_id': self.origin_port_un_location_id.id,
            'default_destination_port_id': self.destination_port_un_location_id.id,
            'default_transport_mode_id': self.transport_mode_id.id,
            'default_master_shipment_id': self.id,
            'default_carrier_id': self.shipping_line_id.id,
            'default_flight_number': self.voyage_number,
        }
        return {
            'name': _('Find Flight from Schedule'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'air.schedule.selector.wizard',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
