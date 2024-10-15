# -*- coding: utf-8 -*-

from odoo import models, fields, _


class WizardPublishQuoteConfirmation(models.TransientModel):
    _name = "wizard.publish.quote.confirmation"
    _description = "Publish Quote Confirmation"

    shipment_quote_id = fields.Many2one('shipment.quote', required=True)

    def action_send_email(self):
        return self.shipment_quote_id.action_quote_send()

    def action_publish_quote(self):
        return self.shipment_quote_id.action_publish_quote()
