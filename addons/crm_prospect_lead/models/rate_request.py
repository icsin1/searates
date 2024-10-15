# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import ValidationError


class RateRequest(models.Model):
    _name = "rate.request"
    _description = "Rate Request"

    name = fields.Char(string='Rate Request Number', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: "New Rate Request Number")
    agent_id = fields.Many2one('res.partner',
                               domain="[('category_ids.name', 'in', ['Agent','Vendor','Consignee','Transporter'])]",
                               string='Agent')
    opportunity_id = fields.Many2one('crm.prospect.opportunity', string='Opportunity')


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _action_send_mail(self, auto_commit=False):
        if self.model == 'crm.prospect.opportunity':
            res_id = self._context.get("active_ids")
            opportunity_id = self.env["crm.prospect.opportunity"].browse(res_id)
            if self.env.context.get('is_rate_request'):
                if not self.partner_ids:
                    raise ValidationError(_("Enter At least One Recipients"))
                opportunity_id._create_rate_request_vals()
        return super(MailComposeMessage, self)._action_send_mail(auto_commit=auto_commit)
