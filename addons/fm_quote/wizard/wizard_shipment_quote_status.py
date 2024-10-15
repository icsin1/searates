# -*- coding: utf-8 -*-

from odoo import models, fields, _


class WizardQuoteStatus(models.TransientModel):
    _name = "wizard.shipment.quote.status"
    _description = "Wizard Quote Status"

    quotation_id = fields.Many2one('shipment.quote', required=True)
    change_reason_id = fields.Many2one('change.reason', string='Reason')
    remark = fields.Text(string='Remarks')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('expire', 'Expired'),
        ('cancel', 'Cancelled'),
        ('accept', 'Accepted'),
        ('reject', 'Rejected')
    ], required=True)

    def action_change_status(self):
        if self.quotation_id:
            # Updating Quotation state
            return self.quotation_id._update_quote_status(self.state, self.change_reason_id, self.remark)
        return True
