# -*- coding: utf-8 -*-

from odoo import models, fields


class WizardShipmentQuoteStatus(models.TransientModel):
    _inherit = "wizard.shipment.quote.status"

    show_cancel_state_only = fields.Boolean()
    quotation_state = fields.Selection(related='quotation_id.state', store=True)
