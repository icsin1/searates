# -*- coding: utf-8 -*-

from odoo import fields, models, api


class FreightHouseShipment(models.Model):
    _inherit = 'freight.house.shipment'

    @api.model_create_single
    def create(self, values):
        shipment = super().create(values)
        # auto fetch services from quote to shipment
        if shipment.shipment_quote_id:
            shipment.action_fetch_quote_services()
        return shipment

    def update_cost_charge_ids(self):
        self.ensure_one()
        house_cost_charge_ids = self.env['house.shipment.charge.cost'].search([('house_shipment_id', '=', self.id)])
        HouseCostChargeObj = self.env['house.shipment.charge.cost']
        for quote_charge in self.shipment_quote_id.quotation_line_ids.filtered(
                lambda ql: not ql.shipment_cost_charge_ids if self.shipment_quote_id.shipment_count == 'single'
                else ql.shipment_cost_charge_ids not in house_cost_charge_ids and ql.shipment_cost_charge_ids.product_id.ids not in house_cost_charge_ids.product_id.ids):
            vals = quote_charge._prepare_charges_cost_value()
            vals.update({'house_shipment_id': self.id})
            shipment_charge = HouseCostChargeObj.create(vals)
            quote_charge.shipment_cost_charge_ids = shipment_charge | quote_charge.mapped('shipment_cost_charge_ids')

    def update_revenue_charge_ids(self):
        self.ensure_one()
        house_revenue_charge_ids = self.env['house.shipment.charge.revenue'].search([('house_shipment_id', '=', self.id)])
        HouseRevenueChargeObj = self.env['house.shipment.charge.revenue']
        for quote_charge in self.shipment_quote_id.quotation_line_ids.filtered(
                lambda ql: not ql.shipment_revenue_charge_ids if self.shipment_quote_id.shipment_count == 'single'
                else ql.shipment_revenue_charge_ids not in house_revenue_charge_ids and ql.product_id.id not in house_revenue_charge_ids.product_id.ids):
            vals = quote_charge._prepare_charges_revenue_value()
            vals.update({'house_shipment_id': self.id})
            shipment_charge = HouseRevenueChargeObj.create(vals)
            quote_charge.shipment_revenue_charge_ids = shipment_charge | quote_charge.mapped('shipment_revenue_charge_ids')

    def action_fetch_quote_services(self):
        self.ensure_one()
        self.update_cost_charge_ids()
        self.update_revenue_charge_ids()


class FreightChargeMixin(models.AbstractModel):
    _inherit = 'mixin.freight.charge'

    quote_line_id = fields.Many2one('shipment.quote.line', copy=False)
