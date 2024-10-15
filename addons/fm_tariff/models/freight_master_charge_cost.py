# -*- coding: utf-8 -*-
from odoo import models, fields, api


class MasterShipmentChargeCost(models.Model):
    _inherit = 'master.shipment.charge.cost'

    buy_tariff_line_id = fields.Many2one('tariff.buy.line')

    @api.model
    def action_tariff_services_wizard(self, shipment_id):
        shipment = self.env['freight.master.shipment'].browse(int(shipment_id))
        return shipment.action_tariff_services_wizard(model=self._name)
