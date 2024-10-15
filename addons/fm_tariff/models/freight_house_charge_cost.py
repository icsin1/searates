# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HouseShipmentChargeCost(models.Model):
    _inherit = 'house.shipment.charge.cost'

    buy_tariff_line_id = fields.Many2one('tariff.buy.line')

    @api.model
    def action_tariff_services_wizard(self, shipment_id):
        shipment = self.env['freight.house.shipment'].browse(int(shipment_id))
        return shipment.action_tariff_services_wizard(model=self._name)
