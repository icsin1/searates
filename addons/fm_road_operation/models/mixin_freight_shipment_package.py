from odoo import models, fields


class FreightShipmentPackageMixin(models.AbstractModel):
    _inherit = 'freight.shipment.package.mixin'

    truck_number_id = fields.Many2one('freight.truck.number', string="Truck No.", inverse="_inverse_truck_number_id")
    trailer_number_id = fields.Many2one('freight.truck.trailer.number', string="Trailer Number")

    def _inverse_truck_number_id(self):
        pass
