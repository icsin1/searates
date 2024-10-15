from odoo import models, fields, _, api


ROAD_STATE = [
    ('draft', 'Created'),
    ('cancelled', 'Cancelled'),
    ('completed', 'Completed'),
]


class WizardMasterShipmentStatus(models.TransientModel):
    _inherit = 'wizard.master.shipment.status'

    road_state = fields.Selection(ROAD_STATE, string='State ')
    mode_type = fields.Selection(related="shipment_id.mode_type")

    @api.onchange('road_state')
    def _onchange_road_state(self):
        for wizard in self:
            wizard.state = wizard.road_state

    def action_change_status(self):
        for wizard in self:
            if wizard.mode_type == "land":
                wizard.state = wizard.road_state
        return super().action_change_status()
