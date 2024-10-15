# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class WizardQuoteMultiCarrierCharges(models.TransientModel):
    _name = 'wizard.quote.multi.carrier.charges'
    _description = 'Wizard Quote Multi Carrier Charges'

    carrier_id = fields.Many2one('freight.carrier', string='Shipping Line')
    incoterm_id = fields.Many2one('account.incoterms', string='Incoterms')
    shipment_quote_id = fields.Many2one('shipment.quote', string='Shipment Quote', required=True)
    transport_mode_id = fields.Many2one('transport.mode')
    mode_type = fields.Selection(related='transport_mode_id.mode_type', store=True)
    include_all_quote_charges = fields.Boolean(default=True)
    shipment_quote_charge_ids = fields.One2many('wizard.quote.multi.carrier.charges.line', 'wizard_quote_multi_carrier_charges_id', string='Charges')

    def action_create_house_shipment(self):
        shipment_quote_charge_ids = self.shipment_quote_charge_ids.filtered(lambda charge: charge.include_charge)
        if not shipment_quote_charge_ids:
            raise ValidationError(_('No charges found to add.'))

        action = self.shipment_quote_id.action_create_shipment()
        default_vals = action['context']
        revenue_charge_ids = self.prepare_house_shipment_revenue_charges(shipment_quote_charge_ids) or []
        cost_charge_ids = self.prepare_house_shipment_cost_charges(shipment_quote_charge_ids) or []
        default_vals.update({'default_shipping_line_id': self.carrier_id.id, 'default_inco_term_id': self.incoterm_id.id, 'default_revenue_charge_ids': revenue_charge_ids,
                             'default_cost_charge_ids': cost_charge_ids})
        action['context'] = default_vals
        return action

    @api.onchange('include_all_quote_charges')
    def _onchange_include_all_quote_charges(self):
        self.shipment_quote_charge_ids.write({'include_charge': self.include_all_quote_charges})

    @api.onchange('carrier_id', 'incoterm_id')
    def _onchange_carrier_incoterm(self):
        self.shipment_quote_charge_ids = [(5, 0, 0)]
        if self.carrier_id and self.incoterm_id:
            charge_lines = []
            quote_lines = self.env['shipment.quote.line'].search([
                ('carrier_id', '=', self.carrier_id.id),
                ('incoterm_id', '=', self.incoterm_id.id),
                ('quotation_id', '=', self.shipment_quote_id.id),
            ])
            for line in quote_lines:
                charge_lines.append((0, 0, self.prepare_quote_charge_vals(line)))
            self.shipment_quote_charge_ids = charge_lines

    def prepare_quote_charge_vals(self, charge_line_id):
        return {
            'shipment_quote_charge_line_id': charge_line_id.id,
            'product_id': charge_line_id.product_id.id,
            'service_name': charge_line_id.service_name,
            'measurement_basis_id': charge_line_id.measurement_basis_id.id,
            'quantity': charge_line_id.quantity,
            'cost_currency_id': charge_line_id.cost_currency_id.id,
            'cost_amount_rate': charge_line_id.cost_amount_rate,
            'sell_currency_id': charge_line_id.sell_currency_id.id,
            'sell_amount_rate': charge_line_id.sell_amount_rate,
        }

    def prepare_house_shipment_revenue_charges(self, shipment_quote_charge_ids):
        return [(0, 0, charge.shipment_quote_charge_line_id._prepare_charges_revenue_value()) for charge in shipment_quote_charge_ids]

    def prepare_house_shipment_cost_charges(self, shipment_quote_charge_ids):
        return [(0, 0, charge.shipment_quote_charge_line_id._prepare_charges_cost_value()) for charge in shipment_quote_charge_ids]
