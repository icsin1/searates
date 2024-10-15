# -*- coding: utf-8 -*-
from odoo import models


class FreightHouseShipment(models.Model):
    _inherit = 'freight.house.shipment'

    def action_fetch_quote_services(self):
        self.ensure_one()
        if self.shipment_quote_id and self.shipment_quote_id.multi_carrier_quote:
            self.update_shipment_revenue_charges_on_quote()
            self.update_shipment_cost_charges_on_quote()
        return super().action_fetch_quote_services()

    def update_shipment_revenue_charges_on_quote(self):
        revenue_charge_ids = self.revenue_charge_ids.filtered(lambda charge: charge.quote_line_id)
        for charge in revenue_charge_ids:
            charge.quote_line_id.shipment_revenue_charge_ids |= charge
        return

    def update_shipment_cost_charges_on_quote(self):
        cost_charge_ids = self.cost_charge_ids.filtered(lambda charge: charge.quote_line_id)
        for charge in cost_charge_ids:
            charge.quote_line_id.shipment_cost_charge_ids |= charge
        return

    def update_revenue_charge_ids(self):
        self.ensure_one()
        if self.shipment_quote_id and self.shipment_quote_id.multi_carrier_quote:
            return
        return super().update_revenue_charge_ids()

    def update_cost_charge_ids(self):
        self.ensure_one()
        if self.shipment_quote_id and self.shipment_quote_id.multi_carrier_quote:
            return
        return super().update_cost_charge_ids()
