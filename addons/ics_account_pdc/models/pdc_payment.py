# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class PDCPayment(models.Model):
    _name = 'pdc.payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "PDC Payment"
    _order = "clearing_date DESC, date DESC"

    @api.depends('payment_id.move_id.line_ids.matched_debit_ids', 'payment_id.move_id.line_ids.matched_credit_ids')
    def _compute_move_ids(self):
        for rec in self:
            move_ids = rec.payment_id.reconciled_invoice_ids + rec.payment_id.reconciled_bill_ids
            rec.move_ids = move_ids.ids

    @api.depends('move_ids')
    def _compute_move_count(self):
        for rec in self:
            rec.move_count = len(rec.move_ids)

    @api.depends('payment_id.payment_method_line_id', 'move_id.line_ids.statement_id', 'move_id.line_ids.full_reconcile_id')
    def _compute_is_reconciled(self):
        for rec in self:
            is_reconciled = False
            if self.payment_id.payment_method_line_id.payment_account_id:
                if rec.payment_id.payment_type == "inbound":
                    pdc_account_id = self.env.company.pdc_receivable_account_id
                elif rec.payment_id.payment_type == "outbound":
                    pdc_account_id = self.env.company.pdc_payable_account_id
                move_lines = rec.move_id.line_ids.filtered(lambda line: line.account_id == pdc_account_id and line.reconciled)
                residual_field = 'amount_residual' if rec.payment_id.currency_id == rec.payment_id.company_id.currency_id else 'amount_residual_currency'
                valid_bank_statement = move_lines.mapped('statement_id').filtered(lambda st: st.state != 'open')
                is_reconciled = rec.payment_id.currency_id.is_zero(sum(move_lines.mapped(residual_field))) and valid_bank_statement
            else:
                account_id = self.env.company.account_journal_payment_debit_account_id.id
                if rec.payment_id.payment_type == "outbound":
                    account_id = self.env.company.account_journal_payment_credit_account_id.id
                move_line = rec.move_id.line_ids.filtered(lambda line: line.account_id.id == account_id)
                valid_bank_statement = move_line.statement_id.filtered(lambda st: st.state != 'open')
                if move_line.full_reconcile_id and valid_bank_statement:
                    is_reconciled = True
            rec.is_reconciled = is_reconciled

    name = fields.Char("Cheque Number", required=1)
    cheque_ref = fields.Char()
    payment_date = fields.Date(required=1)
    move_ids = fields.Many2many('account.move', string="Invoice", compute="_compute_move_ids", store=True, readonly=False)
    payment_id = fields.Many2one('account.payment', string="Payment", ondelete="cascade")
    journal_id = fields.Many2one('account.journal', string="Payment Journal", required=1)
    partner_id = fields.Many2one('res.partner', string="Partner")
    date = fields.Date(required=1, string="Cheque Date")
    currency_id = fields.Many2one('res.currency', related="payment_id.currency_id")
    amount = fields.Monetary("Payment amount")
    state = fields.Selection([('registered', 'Registered'),
                             ('returned', 'Returned'),
                             ('deposited', 'Deposited'),
                             ('bounced', 'Bounced'),
                             ('done', 'Done')], string="Status", default="registered")
    clearing_date = fields.Date()
    move_count = fields.Integer(compute="_compute_move_count", store=True)
    move_id = fields.Many2one('account.move', string="Move")
    is_reconciled = fields.Boolean(compute="_compute_is_reconciled", store=True)
    company_id = fields.Many2one('res.company', string='Company', store=True, readonly=True,
                                 related="payment_id.company_id")
    company_currency_id = fields.Many2one(related='company_id.currency_id', string='Company Currency',
                                          readonly=True, store=True,
                                          help='Utility field to express amount currency')
    amount_company_currency_signed = fields.Monetary(
        currency_field='company_currency_id', related="payment_id.amount_company_currency_signed")

    def _update_pdc_payment_status(self, new_status, clearing_date=None):
        self.ensure_one()
        vals = {
            'state': new_status
        }
        if clearing_date:
            vals.update(clearing_date=clearing_date)
        self.write(vals)

    def reverse_entry(self, reason=None):
        move_ids = self.payment_id.mapped('move_id')
        move_reversal = self.env['account.move.reversal']\
            .with_context(active_model="account.move", active_ids=move_ids.ids).create({
                'date': fields.Date.today(),
                'reason': reason,
                'refund_method': 'cancel',
                'journal_id': move_ids[0].journal_id.id,
            })
        move_reversal.reverse_moves()

    def action_mark_returned(self):
        self.ensure_one()
        self.reverse_entry(reason="Check Returned")
        self.state = "returned"

    def action_mark_deposited(self):
        self.ensure_one()
        self.state = "deposited"

    def action_mark_bounced(self):
        self.ensure_one()
        self.reverse_entry(reason="Check Bounced")
        self.state = "bounced"

    def _prepare_move_line_vals(self):
        self.ensure_one()
        amount = self.amount
        description = "PDC Payment for Cheque: {}".format(self.name)
        if self.currency_id != self.company_id.currency_id:
            amount = self.payment_id.amount_company_currency_signed
        if self.payment_id.payment_type == "outbound":
            account_id = self.payment_id.payment_method_line_id.payment_account_id.id or self.env.company.account_journal_payment_credit_account_id.id
            pdc_account_id = self.env.company.pdc_payable_account_id.id
            return [(0, 0, {
                'debit': 0.0,
                'credit': amount,
                'account_id': account_id,
                'currency_id': self.currency_id.id,
                'partner_id': self.partner_id.id,
                'amount_currency': -self.amount,
                'date_maturity': self.clearing_date,
                'name': description,
            }), (0, 0, {
                'debit': amount,
                'credit': 0.0,
                'account_id': pdc_account_id,
                'currency_id': self.currency_id.id,
                'partner_id': self.partner_id.id,
                'amount_currency': self.amount,
                'date_maturity': self.clearing_date,
                'name': description,
            })]
        else:
            account_id = self.payment_id.payment_method_line_id.payment_account_id.id or self.env.company.account_journal_payment_debit_account_id.id
            pdc_account_id = self.env.company.pdc_receivable_account_id.id
            return [(0, 0, {
                'debit': amount,
                'credit': 0.0,
                'account_id': account_id,
                'currency_id': self.currency_id.id,
                'partner_id': self.partner_id.id,
                'amount_currency': self.amount,
                'date_maturity': self.clearing_date,
                'name': description,
            }), (0, 0, {
                'debit': 0.0,
                'credit': amount,
                'account_id': pdc_account_id,
                'currency_id': self.currency_id.id,
                'partner_id': self.partner_id.id,
                'amount_currency': -self.amount,
                'date_maturity': self.clearing_date,
                'name': description,
            })]

    def _prepare_move_vals(self):
        self.ensure_one()
        vals = {
            'move_type': 'entry',
            'ref': 'PDC Payment',
            'date': self.clearing_date,
            'journal_id': self.payment_id.move_id.journal_id.id,
            'invoice_user_id': self.env.user.id,
            'auto_post': True,
            'line_ids': self._prepare_move_line_vals(),
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
        }
        return vals

    def _create_journal_entry(self):
        self.ensure_one()
        vals = self._prepare_move_vals()
        return self.env['account.move'].create(vals)

    def reconcile_entries(self):
        self.ensure_one()
        pdc_account_id = self.env.company.pdc_receivable_account_id.id
        if self.payment_id.payment_type == "outbound":
            pdc_account_id = self.env.company.pdc_payable_account_id.id
        move_line = self.move_id.line_ids.filtered(lambda line: line.account_id.id == pdc_account_id)
        move_line += self.payment_id.move_id.line_ids.filtered(lambda line: line.account_id.id == pdc_account_id)
        move_line.reconcile()

    def action_mark_done(self):
        self.ensure_one()
        if not self.clearing_date:
            raise ValidationError(_("Clearing Date is required!"))
        move_id = self._create_journal_entry()
        move_id._post()
        self.write({
            'state': 'done',
            'move_id': move_id.id
        })
        self.reconcile_entries()

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res.activity_schedule(
            'mail.mail_activity_data_todo',
            res.date,
            user_id=res.create_uid.id,
        )
        return res

    @api.model
    def _cron_cheque_deposit_reminder(self):
        template_id = self.env.ref('ics_account_pdc.email_template_pdc_payment_reminder')
        not_deposited_cheque = self.search([('state', '=', 'registered')])\
            .filtered(lambda rec: rec.date and fields.Date.today() == rec.date - timedelta(days=1))
        for cheque in not_deposited_cheque:
            cheque.message_post_with_template(template_id.id)

    def action_open_move(self):
        self.ensure_one()
        action = {
            'name': _("Move"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'context': {'create': False},
            'view_mode': 'form',
            'res_id': self.move_id.id,
        }
        return action

    def action_open_invoice(self):
        self.ensure_one()
        action = {
            'name': _("Invoices"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'context': {'create': False},
        }
        if len(self.move_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.move_ids.id,
            })
        else:
            action.update({
                'view_mode': 'list,form',
                'domain': [('id', 'in', self.move_ids.ids)],
            })
        return action

    @api.model
    def _get_pdc_receivable_code(self, company):
        company_id = "{:02d}".format(company.id)
        return "11{CompanyID}63".format(CompanyID=company_id)

    @api.model
    def _get_pdc_payable_code(self, company):
        company_id = "{:02d}".format(company.id)
        return "11{CompanyID}64".format(CompanyID=company_id)
