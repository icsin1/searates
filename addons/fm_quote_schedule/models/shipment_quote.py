from odoo import models, fields
from odoo.addons.fm_quote.models.shipment_quote import READONLY_STAGE


class ShipmentQuote(models.Model):
    _inherit = 'shipment.quote'

    add_vessel_details = fields.Boolean(states=READONLY_STAGE, readonly=True)
    schedule_ids = fields.Many2many('freight.schedule', 'shipment_quote_freight_schedule_rel', copy=False, states=READONLY_STAGE, readonly=True)
