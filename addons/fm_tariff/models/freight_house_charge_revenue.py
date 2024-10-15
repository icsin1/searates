# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HouseShipmentChargeRevenue(models.Model):
    _inherit = 'house.shipment.charge.revenue'

    sell_tariff_line_id = fields.Many2one('tariff.sell.line')

    @api.model
    def action_tariff_services_wizard(self, shipment_id):
        shipment = self.env['freight.house.shipment'].browse(int(shipment_id))
        return shipment.action_tariff_services_wizard(model=self._name)
