# -*- coding: utf-8 -*-
from odoo import fields, models


class ShipmentQuoteLine(models.Model):
    _inherit = "shipment.quote.line"

    house_shipment_id = fields.Many2one('freight.house.shipment', copy=False)

    # before remove this field it used in migration script so later we can remove this two field
    shipment_cost_charge_id = fields.Many2one('house.shipment.charge.cost', copy=False)
    shipment_revenue_charge_id = fields.Many2one('house.shipment.charge.revenue', copy=False)

    shipment_cost_charge_ids = fields.Many2many('house.shipment.charge.cost', 'house_shipment_charge_cost_shipment_quote_line_rel', 'shipment_quote_line_id',
                                                'house_shipment_charge_cost_id', copy=False, string='Cost Charges')
    shipment_revenue_charge_ids = fields.Many2many('house.shipment.charge.revenue', 'house_shipment_charge_revenue_shipment_quote_line_rel', 'shipment_quote_line_id',
                                                   'house_shipment_charge_revenue_id', copy=False, string='Revenue Charges')

    def _prepare_charges_revenue_value(self):
        self.ensure_one()
        if self.debtor_partner_id:
            partner, partner_address = self.debtor_partner_id, self.debtor_address_id
        else:
            partner, partner_address = self.quotation_id.client_id, self.quotation_id.client_address_id
        revenue_vals = {
            'product_id': self.product_id.id,
            'charge_description': self.service_name,
            'quantity': self.quantity,
            'measurement_basis_id': self.measurement_basis_id.id,
            'container_type_id': self.container_type_id.id,
            'partner_id': partner.id,
            'partner_address_id': partner_address.id,
            'amount_currency_id': self.sell_currency_id.id,
            'amount_conversion_rate': self.sell_conversion_rate,
            'amount_rate': self.sell_amount_rate,
            'tax_ids': [(6, 0, self.tax_ids.ids)],
            'remarks': self.sell_remarks,
            'quote_line_id': self.id,
            'property_account_id': self.property_account_income_id.id
        }
        return revenue_vals

    def _prepare_charges_cost_value(self):
        self.ensure_one()
        cost_vals = {
            'product_id': self.product_id.id,
            'charge_description': self.service_name,
            'quantity': self.quantity,
            'measurement_basis_id': self.measurement_basis_id.id,
            'container_type_id': self.container_type_id.id,
            'partner_id': self.creditor_partner_id.id,
            'partner_address_id': self.creditor_address_id.id,
            'amount_currency_id': self.cost_currency_id.id,
            'amount_conversion_rate': self.cost_conversion_rate,
            'amount_rate': self.cost_amount_rate,
            'tax_ids': [(6, 0, self.supplier_tax_ids.ids)],
            'remarks': self.cost_remarks,
            'quote_line_id': self.id,
            'property_account_id': self.property_account_expense_id.id
        }
        return cost_vals
