
from odoo import models, fields


class AdjustPaymentWizardLine(models.TransientModel):
    _inherit = 'adjust.payment.wizard.line'

    house_shipment_ids = fields.Many2many('freight.house.shipment', related='move_id.house_shipment_ids')
