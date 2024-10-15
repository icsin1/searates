# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.addons.fm_quote.models.shipment_quote import STATES

READONLY_STAGE = {'draft': [('readonly', False)]}
STATES.insert(1, ('to_approve', 'To Approve'))
STATES.insert(2, ('approved', 'Approved'))


class ShipmentQuote(models.Model):
    _inherit = "shipment.quote"

    @api.depends('approving_user_id', 'user_id', 'user_id.approver_id', 'user_id.is_approval_authority')
    def _compute_allow_approval(self):
        for quote in self:
            quote.allow_approval = False if not self.approving_user_id or self.env.user.sudo().is_approval_authority or quote.approving_user_id.id == quote.user_id.id else True

    state = fields.Selection(selection_add=STATES)
    allow_approval = fields.Boolean(compute='_compute_allow_approval', store=True)
    approving_user_id = fields.Many2one(
        'res.users', string="Quote Approver", default=lambda self: self.env.user.sudo().approver_id, states=READONLY_STAGE, tracking=True, readonly=True,
        domain=lambda self: "[('groups_id', '=', {})]".format(self.env.ref('freight_base.group_user_freight_approver_team', raise_if_not_found=False).id)
    )
    approver_reject_reason = fields.Char(copy=False, readonly=True)
    is_margin_percent = fields.Boolean(string="Is Margin Percentage ?", compute="compute_is_margin_percent")

    def compute_is_margin_percent(self):
        for rec in self:
            is_margin_percent = False
            if rec.company_id.margin_percent or rec.company_id.margin_revenue:
                is_margin_percent = True
            rec.is_margin_percent = is_margin_percent

    def send_email_to_approver(self):
        self.ensure_one()
        mail_template = self.env.ref('fm_quote_approval.quote_approval_email_template')
        mail_template.send_mail(self.id, force_send=True)

    def check_margin_revenue(self):
        self.ensure_one()
        if self.company_id.margin_percent or self.company_id.margin_revenue:
            state = self.state
            if self.company_id.margin_percent and not self.company_id.margin_revenue:
                if round(self.estimated_margin_percent, 2) >= self.company_id.margin_percent:
                    state = 'approved'
                elif round(self.estimated_margin_percent, 2) < self.company_id.margin_percent:
                    state = 'to_approve'
                    self.send_email_to_approver()

            if not self.company_id.margin_percent and self.company_id.margin_revenue:
                if round(self.estimated_total_revenue, 2) >= self.company_id.margin_revenue:
                    state = 'to_approve'
                    self.send_email_to_approver()
                elif round(self.estimated_total_revenue, 2) < self.company_id.margin_revenue:
                    state = 'approved'

            if self.company_id.margin_percent and self.company_id.margin_revenue:
                if round(self.estimated_margin_percent, 2) >= self.company_id.margin_percent and self.estimated_total_revenue < self.company_id.margin_revenue:
                    state = 'approved'
                elif round(self.estimated_margin_percent, 2) >= self.company_id.margin_percent and self.estimated_total_revenue >= self.company_id.margin_revenue:
                    state = 'to_approve'
                    self.send_email_to_approver()
                elif (self.estimated_margin_percent and not self.company_id.margin_percent) and (self.estimated_total_revenue and not self.company_id.margin_revenue):
                    state = 'to_approve'
                    self.send_email_to_approver()
                elif round(self.estimated_margin_percent, 2) < self.company_id.margin_percent and self.estimated_total_revenue < self.company_id.margin_revenue:
                    state = 'to_approve'
                    self.send_email_to_approver()
                elif round(self.estimated_margin_percent, 2) < self.company_id.margin_percent and self.estimated_total_revenue >= self.company_id.margin_revenue:
                    state = 'to_approve'
                    self.send_email_to_approver()

            self.with_context(is_quote_create=True).state = state
            state_name = dict(self._fields['state'].selection).get(state)
            self.message_post(body=_(
                """Quote auto <strong>%s</strong> by <strong>%s</strong>""" % (state_name, self.env.user.name))
            )

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        return super(ShipmentQuote, self.with_context(is_quote_copy=True)).copy(default=default)

    @api.model_create_single
    def create(self, values):
        rec = super().create(values)
        if (values.get('quotation_line_ids') or rec.quotation_line_ids) and rec.state == 'draft' and not self.env.context.get('is_quote_copy'):
            rec.check_margin_revenue()
        if self.env.user.has_group('fm_quote_approval.quote_direct_accept_group_access') and not self.env.context.get('is_quote_copy'):
            rec.move_quote_to_accept_state()
        return rec

    def move_quote_to_accept_state(self):
        self.state = 'accept'
        self._track_template(['state'])
        field = self.fields_get('state')
        tracking_value_ids = self._mail_track(field, {'state': 'draft'})
        if tracking_value_ids and tracking_value_ids[1]:
            self._message_log(tracking_value_ids=tracking_value_ids[1])

    def write(self, vals):
        res = super().write(vals)
        context = self.env.context
        if not context.get('is_quote_create'):
            for quote in self:
                if ('quotation_line_ids' in vals or quote.quotation_line_ids) and quote.state == 'draft' and not context.get('is_quote_copy'):
                    quote.check_margin_revenue()
        return res

    def _update_quote_status(self, new_status, change_reason_id=None, remark=None):
        self.ensure_one()
        if new_status == 'draft':
            self.write({'approver_reject_reason': False})
        return super()._update_quote_status(new_status, change_reason_id=change_reason_id, remark=remark)

    def approve_quote_internal_team(self):
        self.ensure_one()
        if self.state in ['draft', 'expire', 'cancel', 'reject']:
            raise ValidationError(_("Quote status is changed to %s, You can not approve quote. when status is other than to-approve") % (str(self.state).title()))
        self.write({'state': 'approved'})
        quote_approval_type = self.env.ref('fm_quote_approval.mail_activity_type_quote_approval')
        quote_activity = self.env['mail.activity'].search([('res_id', '=', self.id),
                                                           ('res_model', '=', 'shipment.quote'),
                                                           ('activity_type_id', '=', quote_approval_type.id)])
        quote_activity.action_done()
        self.message_post(body=_("""Quotation:%s <strong>"Approved"</strong> by <strong>%s</strong>""" % (self.name, self.env.user.name)))

    def reject_quote_internal_team(self):
        self.ensure_one()
        if self.state in ['draft', 'expire', 'cancel', 'reject']:
            raise ValidationError(_("Quote status is changed to %s, You can not reject quote. when status is other than to-approve") % (str(self.state).title()))
        wiz_rec = self.env['shipment.quote.reject.reason'].create({'quote_id': self.id})
        return {
            'name': 'Quote Rejection with Reason',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'shipment.quote.reject.reason',
            'target': 'new',
            'res_id': wiz_rec.id
        }

    def action_send_quote_internal_approval(self):
        self.ensure_one()
        self.ensure_quote_approval()

        template_id = self.env['ir.model.data']._xmlid_to_res_id('fm_quote_approval.shipment_quote_approval_email_template', raise_if_not_found=False)
        ctx = {
            'default_model': self._name,
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_light",
            'mark_quote_as_sent_approval': True,
        }
        return {
            'name': 'Quote: Mail Composer',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_quote_as_sent'):
            self.filtered(lambda o: o.state == 'approved').write({'state': 'sent'})
        if self.env.context.get('mark_quote_as_sent_approval'):
            self.env['mail.activity'].create({
                'summary': 'Shipment Quote: Approval Reminder',
                'activity_type_id': self.env.ref('fm_quote_approval.mail_activity_type_quote_approval').id,
                'res_model_id': self.env['ir.model']._get_id('shipment.quote'),
                'user_id': self.approving_user_id.id,
                'res_id': self.id
            })
            self.filtered(lambda o: o.state == 'draft').write({'state': 'to_approve'})
        return super(ShipmentQuote, self.with_context(mail_post_autofollow=self.env.context.get('mail_post_autofollow', True))).message_post(**kwargs)

    def action_change_status(self):
        res = super().action_change_status()
        if self.state in ['draft', 'to_approve'] and not self.env.user.has_group('fm_quote_approval.quote_direct_accept_group_access'):
            context = res['context'].copy()
            context.update({'default_state': 'cancel', 'default_show_cancel_state_only': True})
            res['context'] = context

        return res
