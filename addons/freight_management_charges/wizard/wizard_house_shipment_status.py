# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import ValidationError


class WizardHouseShipmentStatus(models.TransientModel):
    _inherit = 'wizard.house.shipment.status'

    def action_change_status(self):
        self.ensure_one()
        state = self.state
        shipment = self.shipment_id
        if not shipment or shipment.state == state:
            return True
        billed_cost_charge_ids = shipment.cost_charge_ids.filtered(lambda charge: charge.status != 'no')
        invoiced_revenue_charge_ids = shipment.revenue_charge_ids.filtered(lambda charge: charge.status != 'no')
        if state == 'cancelled' and (billed_cost_charge_ids or invoiced_revenue_charge_ids):
            raise ValidationError(_("You cannot cancel a House-shipment once invoices or vendor bills have been generated."))
        return super().action_change_status()
