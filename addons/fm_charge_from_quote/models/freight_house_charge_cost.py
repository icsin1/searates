from odoo import models, api, _
from odoo.exceptions import ValidationError


class HouseShipmentChargeCost(models.Model):
    _inherit = 'house.shipment.charge.cost'

    @api.model
    def update_cost_charge_ids(self, shipment_id):
        shipment = self.env['freight.house.shipment'].browse(int(shipment_id))
        if shipment and not shipment.shipment_quote_id:
            raise ValidationError(_('Shipment-%s is not Generated from Quote.') % (shipment.name))
        shipment.update_cost_charge_ids()
