
from odoo import models


class HouseShipmentChargeCost(models.Model):
    _inherit = 'house.shipment.charge.cost'

    def unlink(self):
        master_attached_rec = self.filtered(lambda rec: rec.master_shipment_cost_charge_id and rec.master_shipment_cost_charge_id.house_shipment_id)
        if master_attached_rec:
            master_attached_rec.mapped('master_shipment_cost_charge_id').with_context(unlink_house_charge=True).house_shipment_id = False
        super().unlink()
