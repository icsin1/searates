# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import ValidationError


class WizardMasterShipmentStatus(models.TransientModel):
    _inherit = 'wizard.master.shipment.status'

    def action_change_status(self):
        self.ensure_one()
        state = self.state
        if self.mode_type == 'air':
            state = self.air_state
        shipment = self.shipment_id
        if not shipment or shipment.state == state:
            return True
        adjusted_cost_charge_ids = shipment.cost_charge_ids.filtered(lambda charge: charge.status != 'no')
        adjusted_revenue_charge_ids = shipment.revenue_charge_ids.filtered(lambda charge: charge.status != 'no')
        if state == 'cancelled' and (adjusted_cost_charge_ids or adjusted_revenue_charge_ids):
            raise ValidationError(_("You cannot cancel a Master-shipment once charge-adjusted to House Shipment."))
        if state == 'cancelled' and shipment.generate_invoice_from_master and shipment.compute_move_ids:
            raise ValidationError(_("You cannot cancel a Master-shipment once Invoice generated."))
        return super().action_change_status()
