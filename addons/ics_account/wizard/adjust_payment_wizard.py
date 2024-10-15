from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import formatLang


class AdjustPaymentWizard(models.TransientModel):
    _name = 'adjust.payment.wizard'
    _description = 'Adjust Payment Wizard'

    @api.depends('payment_id')
    def _compute_move_type(self):
        for wizard in self:
            move_type = False
            if wizard.payment_id.payment_type == "outbound":
                move_type = "in_invoice"
            elif wizard.payment_id.payment_type == "inbound":
                move_type = "out_invoice"
            wizard.move_type = move_type

    @api.depends('payment_id')
    def _compute_line_ids(self):
        for wizard in self:
            vals = []
            move_line_domain = wizard.get_invoice_bill_move_lines()
            move_line_ids = self.env['account.move.line'].search(move_line_domain)
            for line in move_line_ids:
                vals.append((0, 0, {
                    'move_id': line.move_id.id,
                    'partner_id': self.partner_id.id,
                    'move_line_id': line.id
                }))
            wizard.line_ids = vals

    @api.depends('remaining_amount_signed')
    def _compute_remaining_amount(self):
        for record in self:
            remaining_amount = record.remaining_amount_signed
            if record.currency_id != record.company_currency_id:
                remaining_amount = record.company_currency_id._convert(
                    record.remaining_amount_signed,
                    record.currency_id,
                    record.company_id,
                    record.payment_id.date,
                )
            record.remaining_amount = remaining_amount

    @api.depends('company_currency_id', 'currency_id')
    def _compute_diff_currency(self):
        for record in self:
            record.diff_currency = record.company_currency_id != record.currency_id

    @api.depends('line_ids.amount_residual_signed', 'remaining_amount')
    def _compute_remaining_balance(self):
        for record in self:
            adjusted_amount = sum(record.line_ids.mapped('amount_residual_signed'))
            record.remaining_balance = record.remaining_amount_signed - adjusted_amount

    payment_id = fields.Many2one('account.payment')
    move_type = fields.Selection([('out_invoice', 'Invoice'), ('in_invoice', 'Bill')], compute="_compute_move_type")
    invoice_ids = fields.Many2many('account.move', string="Invoices/Bills")
    partner_id = fields.Many2one('res.partner')
    currency_id = fields.Many2one('res.currency', related='payment_id.currency_id', store=True)
    company_id = fields.Many2one(related="payment_id.company_id", string='Company', store=True)
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True,
                                          related='payment_id.company_currency_id')
    remaining_amount = fields.Monetary(string='Remaining Amount', compute="_compute_remaining_amount")
    remaining_amount_signed = fields.Monetary(string='Remaining Balance Signed',
                                              currency_field='company_currency_id')
    multi_select_option = fields.Boolean(string='Multi Select')
    line_ids = fields.One2many('adjust.payment.wizard.line', 'adjust_payment_wizard_id',
                               compute="_compute_line_ids", readonly=False, store=True)
    remaining_balance = fields.Monetary(compute="_compute_remaining_balance", currency_field='company_currency_id')
    diff_currency = fields.Boolean(compute="_compute_diff_currency")

    def action_adjust_payment(self):
        self.ensure_one()
        invoice_data = [{
            'move_id': inv.move_id,
            'amount': inv.amount_residual_signed,
            'amount_with_symbol': formatLang(self.env, inv.amount_residual_signed, currency_obj=inv.company_currency_id),
            'move_line_id': inv.move_line_id
        } for inv in self.line_ids if inv.is_checked]
        self.payment_id._adjust_payment(invoice_data)
        message = _('Payment adjusted <br/>')
        for idx, inv in enumerate(invoice_data, start=1):
            message += f"{idx}. {inv['move_id'].name} <strong> {inv['amount_with_symbol']} </strong><br/>"
        if message:
            self.payment_id.message_post(body=_(message))

    @api.onchange('multi_select_option')
    def _onchange_multi_select_option(self):
        if self.multi_select_option:
            self.line_ids.is_checked = True
        else:
            self.line_ids.is_checked = False

    @api.constrains('line_ids', 'remaining_amount')
    def _check_remaining_amount(self):
        for wiz in self:
            amount_due_total = sum(list(wiz.line_ids.mapped('amount_residual_signed')))
            if amount_due_total > wiz.remaining_amount_signed:
                raise ValidationError(_("Total of Amount Due should not be greater than Balance Amount."))
            amount_due_validation = wiz.line_ids\
                .filtered(lambda line: line.actual_amount_due < line.amount_residual_signed)
            if amount_due_validation:
                raise ValidationError(_("Amount due should not be greater than the actual amount due."))
            invalid_amount_due = wiz.line_ids.filtered(
                lambda line: line.amount_residual_signed <= 0 and line.is_checked)
            if invalid_amount_due:
                raise ValidationError(_("Amount due should be greater than 0."))

    def get_invoice_bill_move_lines(self):
        if self.payment_id.partner_type == "customer":
            internal_type = 'receivable'
        elif self.payment_id.partner_type == "supplier":
            internal_type = 'payable'
        if self.payment_id.payment_type == "outbound":
            operator = '<'
        else:
            operator = '>'

        domain = [('partner_id', '=', self.partner_id.id), ('id', 'not in', self.payment_id.move_id.line_ids.ids),
                  ('company_id', '=', self.payment_id.company_id.id), ('parent_state', '=', 'posted'),
                  ('account_id.internal_type', '=', internal_type), ('balance', operator, 0.0),
                  ('full_reconcile_id', '=', False), ('account_id.reconcile', '=', True),
                  ('amount_residual_currency', '!=', 0.0)]
        if not self.company_id.enable_adjust_payment_multi_currency:
            domain += [('currency_id', '=', self.currency_id.id)]
        return domain


class AdjustPaymentWizardLine(models.TransientModel):
    _name = 'adjust.payment.wizard.line'
    _description = 'Adjust Payment Wizard Line'

    @api.depends('move_line_id', 'is_checked')
    def _compute_amount_residual_signed(self):
        for line in self:
            source_amount_currency = abs(line.move_line_id.amount_residual)
            line.actual_amount_due = source_amount_currency
            line.amount_residual_signed = source_amount_currency if line.is_checked else 0.00

    @api.depends('move_line_id')
    def _compute_amount_total(self):
        for line in self:
            amount_type = 'debit' if line.adjust_payment_wizard_id.payment_id.payment_type == 'inbound' else 'credit'
            company_currency_amount = abs(line.move_line_id[amount_type])
            source_amount = line.company_currency_id._convert(
                company_currency_amount,
                line.currency_id,
                line.company_id,
                line.move_id.invoice_date or line.move_id.date
            )
            line.amount_total = source_amount
            line.amount_total_signed = company_currency_amount

    adjust_payment_wizard_id = fields.Many2one('adjust.payment.wizard')
    move_id = fields.Many2one('account.move', string="Number")
    currency_id = fields.Many2one('res.currency', related='adjust_payment_wizard_id.currency_id', store=True)
    company_currency_id = fields.Many2one(related='adjust_payment_wizard_id.company_currency_id', store=True)
    company_id = fields.Many2one('res.company', related='move_id.company_id', store=True)
    partner_id = fields.Many2one('res.partner', string="Partner")
    invoice_date = fields.Date(related='move_id.invoice_date', store=True)
    amount_total = fields.Monetary('Total', compute="_compute_amount_total")
    amount_total_signed = fields.Monetary('Total Signed', compute="_compute_amount_total",
                                          currency_field='company_currency_id')
    payment_state = fields.Selection(related="move_id.payment_state")
    state = fields.Selection(string='Status', related="move_id.state")
    actual_amount_due = fields.Monetary(compute="_compute_amount_residual_signed", store=True,
                                        currency_field='company_currency_id')
    is_checked = fields.Boolean(string='Select')
    amount_residual_signed = fields.Monetary("Amount Due", readonly=False, store=True,
                                             compute="_compute_amount_residual_signed",
                                             currency_field='company_currency_id')
    move_line_id = fields.Many2one('account.move.line', copy=False)

    @api.onchange('amount_residual_signed')
    def _onchange_amount_residual_signed(self):
        if self.amount_residual_signed > self.amount_total_signed:
            return {
                'warning': {
                    'title': _("Warning"),
                    'message': _("Amount due should not be greater than total signed amount.")
                }
            }
        if self.amount_residual_signed < 0:
            return {
                'warning': {
                    'title': _("Warning"),
                    'message': _("Amount due should not be negative.")
                }
            }
