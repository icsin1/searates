# -*- coding: utf-8 -*-
from odoo import models


class WizardQuoteMultiCarrierCharges(models.TransientModel):
    _inherit = 'wizard.quote.multi.carrier.charges'

    def action_create_house_shipment(self):
        action = super().action_create_house_shipment()
        if self.shipment_quote_id.create_shipment_for == 'house_shipment' and self.env.context.get('from_direct_shipment'):
            default_vals = action['context'].copy()
            default_vals.update({'default_is_quote_direct_shipment': True, 'default_is_direct_shipment': True})
            action['context'] = default_vals
        return action
