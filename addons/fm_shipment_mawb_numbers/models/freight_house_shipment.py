from odoo import models, fields


class FreightHouseShipment(models.Model):
    _inherit = "freight.house.shipment"

    mawb_stock_line_ids = fields.One2many('mawb.stock.line', 'house_shipment_id', string="MAWB Stocks")
