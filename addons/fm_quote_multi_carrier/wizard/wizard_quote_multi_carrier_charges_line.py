# -*- coding: utf-8 -*-
from odoo import models, fields


class WizardQuoteMultiCarrierChargesLine(models.TransientModel):
    _name = 'wizard.quote.multi.carrier.charges.line'
    _description = 'Wizard Quote Multi Carrier Charges Line'

    wizard_quote_multi_carrier_charges_id = fields.Many2one('wizard.quote.multi.carrier.charges', string='Multi Carrier Charges')
    shipment_quote_charge_line_id = fields.Many2one('shipment.quote.line', string='Shipment Quote Charge')
    include_charge = fields.Boolean(default=True)
    product_id = fields.Many2one('product.product', string='Charge Type', required=True)
    service_name = fields.Char(string='Charge Name', required=True)
    measurement_basis_id = fields.Many2one('freight.measurement.basis', string='Measurement Basis', required=True)
    quantity = fields.Float(string='No of Units', required=True, digits='Product Unit of Measure')
    cost_currency_id = fields.Many2one('res.currency', string='Cost Currency', required=True)
    cost_amount_rate = fields.Monetary(string='Cost Rate per Unit', currency_field='cost_currency_id')
    sell_currency_id = fields.Many2one('res.currency', string='Sell Currency', required=True)
    sell_amount_rate = fields.Monetary(string='Sell Rate per Unit', currency_field='sell_currency_id')
