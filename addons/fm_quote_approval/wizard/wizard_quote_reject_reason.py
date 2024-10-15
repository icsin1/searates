# -*- coding: utf-8 -*-
from odoo import models, fields, _


class ShipmentQuoteRejectReason(models.TransientModel):
    _name = 'shipment.quote.reject.reason'
    _description = 'Shipment Quote Reject Reason'

    quote_id = fields.Many2one('shipment.quote')
    reason = fields.Text()

    def submit_rejection(self):
        self.quote_id.write({'state': 'reject', 'approver_reject_reason': self.reason})
        quote_approval_type = self.env.ref('fm_quote_approval.mail_activity_type_quote_approval')
        quote_activity = self.env['mail.activity'].search([('res_id', '=', self.quote_id.id),
                                                           ('res_model', '=', 'shipment.quote'),
                                                           ('activity_type_id', '=', quote_approval_type.id)])
        quote_activity.action_done()
        self.quote_id.message_post(
            body=_("""Quotation:%s <strong>"Rejected"</strong> by %s due to <strong>%s</strong>""" % (self.quote_id.name, self.env.user.name, self.reason)))
