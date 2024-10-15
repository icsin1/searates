from odoo import models, fields, api


class FreightShipmentEventMixin(models.AbstractModel):
    _name = 'freight.shipment.event.mixin'
    _description = 'Freight Shipment Event Mixin'
    _order = 'actual_datetime DESC,estimated_datetime DESC'

    event_type_id = fields.Many2one('freight.event.type', required=True)
    location = fields.Char(string='Place')
    description = fields.Text(string='Description')
    estimated_datetime = fields.Datetime(string='EDT')
    actual_datetime = fields.Datetime(string='ADT')
    public_visible = fields.Boolean(string='Public Tracking Event', default=False)

    @api.onchange('event_type_id')
    def _onchange_event_type_id(self):
        for rec in self:
            rec.public_visible = rec.event_type_id.public_visible
