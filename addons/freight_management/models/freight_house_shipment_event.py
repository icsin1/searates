from odoo import models, fields, api


class FreightHouseShipmentEvent(models.Model):
    _name = 'freight.house.shipment.event'
    _inherit = ['freight.shipment.event.mixin']
    _description = 'House Shipment Milestone'

    shipment_id = fields.Many2one('freight.house.shipment', required=True, ondelete='cascade')
    master_shipment_id = fields.Many2one('freight.master.shipment')
    master_shipment_event_id = fields.Many2one('freight.master.shipment.event', ondelete='cascade')

    def _prepare_event_values(self):
        self.ensure_one()
        return {
            'event_type_id': self.event_type_id.id,
            'location': self.location,
            'description': self.description,
            'estimated_datetime': self.estimated_datetime,
            'actual_datetime': self.actual_datetime,
            'public_visible': self.public_visible,
            'shipment_id': self.shipment_id.id,
            'house_shipment_event_id': self.id,
        }

    def attach_event_to_master(self):
        for event in self:
            master_shipment_id = event.shipment_id.parent_id
            if master_shipment_id and event not in master_shipment_id.mapped('event_ids.house_shipment_event_id'):
                master_shipment_id.write({'event_ids': [(0, 0, event._prepare_event_values())]})

    @api.model_create_single
    def create(self, vals):
        res = super().create(vals)
        if res.master_shipment_event_id:
            res.master_shipment_event_id.write({'house_shipment_event_id': res.id})
        if res.shipment_id.is_direct_shipment:
            res.attach_event_to_master()
        return res
