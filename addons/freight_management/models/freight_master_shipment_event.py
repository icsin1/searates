from odoo import models, fields, api


class FreightMasterShipmentEvent(models.Model):
    _name = 'freight.master.shipment.event'
    _inherit = ['freight.shipment.event.mixin']
    _description = 'House Shipment Milestone'

    shipment_id = fields.Many2one('freight.master.shipment', required=True, ondelete='cascade')
    house_shipment_event_id = fields.Many2one('freight.house.shipment.event', ondelete='cascade')
    event_type_id = fields.Many2one('freight.event.type', related='house_shipment_event_id.event_type_id', readonly=False, store=True)
    location = fields.Char(string='Place', related='house_shipment_event_id.location', readonly=False, store=True)
    description = fields.Text(string='Description', related='house_shipment_event_id.description', readonly=False, store=True)
    estimated_datetime = fields.Datetime(string='EDT', related='house_shipment_event_id.estimated_datetime', readonly=False, store=True)
    actual_datetime = fields.Datetime(string='ADT', related='house_shipment_event_id.actual_datetime', readonly=False, store=True)
    public_visible = fields.Boolean(string='Public Tracking Event', default=False, related='house_shipment_event_id.public_visible', readonly=False, store=True)

    def _prepare_event_values(self):
        self.ensure_one()
        return {
            'event_type_id': self.event_type_id.id,
            'location': self.location,
            'description': self.description,
            'estimated_datetime': self.estimated_datetime,
            'actual_datetime': self.actual_datetime,
            'public_visible': self.public_visible,
            'master_shipment_id': self.shipment_id.id,
            'master_shipment_event_id': self.id,
        }

    def attach_event_to_house(self):
        for event in self:
            house_shipment_ids = event.shipment_id.house_shipment_ids
            if house_shipment_ids:
                house_event_not_exist = house_shipment_ids.filtered(
                    lambda house: event not in house.mapped('event_ids.master_shipment_event_id'))
                if house_event_not_exist:
                    event_vals = event._prepare_event_values()
                    house_event_not_exist.write({
                        'event_ids': [(0, 0, event_vals)]
                    })

    @api.model_create_single
    def create(self, vals):
        res = super().create(vals)
        if res.house_shipment_event_id:
            res.house_shipment_event_id.write({'master_shipment_event_id': res.id})
        if res.shipment_id.is_direct_shipment:
            res.attach_event_to_house()
        house_event = res.shipment_id.house_shipment_ids.event_ids.filtered(
            lambda event: event.master_shipment_event_id.id == res.id)
        if house_event and len(house_event) == 1:
            res.house_shipment_event_id = house_event.id
        return res
