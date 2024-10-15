from odoo import models, fields


class FreightShipmentEventMixin(models.AbstractModel):
    _inherit = 'freight.shipment.event.mixin'

    container_id = fields.Many2one("freight.master.shipment.container.number", "Container Number")
    cargoes_flow_event = fields.Boolean(default=False)
    cargoes_flow_shipment_number = fields.Char()
