# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ShipmentQuote(models.Model):
    _inherit = "shipment.quote"

    multi_carrier_quote = fields.Boolean(copy=False)

    @api.constrains('multi_carrier_quote', 'shipment_count')
    def _check_quote_with_multiple_shipments(self):
        for record in self:
            if record.multi_carrier_quote and record.shipment_count != 'multiple':
                raise ValidationError(_('Multi carrier quote only works with multiple shipments.'))

    @api.onchange('multi_carrier_quote')
    def onchange_multi_carrier_quote(self):
        if self.multi_carrier_quote:
            self.shipment_count = 'multiple'
            self.quote_for = 'shipment'

    @api.onchange('quote_for')
    def _onchange_quote_for_field(self):
        if self.quote_for == 'job':
            self.multi_carrier_quote = False

    def action_quote_multi_carrier_shipment(self):
        if not self.multi_carrier_quote:
            return
        view_id = self.env.ref('fm_quote_multi_carrier.view_wizard_quote_multi_carrier_charges_form')
        return {
            'name': _('Shipment Quote Charges'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'wizard.quote.multi.carrier.charges',
            'views': [(view_id.id, 'form')],
            'target': 'new',
            'context': {
                'default_shipment_quote_id': self.id,
                'default_transport_mode_id': self.transport_mode_id.id,
                'incoterm_ids': self.quotation_line_ids.mapped('incoterm_id').ids,
                'carrier_ids': self.quotation_line_ids.mapped('carrier_id').ids,
                **self.env.context
                }
        }
