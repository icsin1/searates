from odoo import models, fields, _
from odoo.addons.fm_quote.models.shipment_quote import READONLY_STAGE


class ShipmentQuote(models.Model):
    _inherit = 'shipment.quote'

    add_flight_details = fields.Boolean(states=READONLY_STAGE, readonly=True)
    air_schedule_ids = fields.Many2many('freight.air.schedule', 'shipment_quote_freight_air_schedule_rel','quote_id','air_schedule_id', copy=False, states=READONLY_STAGE, readonly=True)
