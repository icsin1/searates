from odoo import models, _


class ShipmentQuote(models.Model):
    _inherit = 'shipment.quote'

    def action_import_sailing_schedule(self):
        ctx = {
            'default_transport_mode_id': self.transport_mode_id.id,
            'default_origin_port_id': self.port_of_loading_id.id,
            'default_destination_port_id': self.port_of_discharge_id.id,
            'default_shipment_date': self.date,
            'default_source': 'inttra',
            'default_shipment_quote_id': self.id,
        }
        return {
            'name': _('Import Sailing Schedule'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'inttra.schedule.search.wizard',
            'target': 'new',
            'context': ctx
            }
