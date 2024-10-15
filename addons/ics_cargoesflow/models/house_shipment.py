from odoo import models


class FreightHouseShipment(models.Model):
    _inherit = 'freight.house.shipment'

    """
        In case of air shipment, we want to track the master shipment number (MAWB) from house shipment also
        So, we have implemented this method
    """
    def action_track_air_shipment(self):
        result_data = {}
        if self.parent_id:
            result_data = self.parent_id.action_track_air_shipment()
        return result_data
