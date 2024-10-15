from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _get_move_line_domain(self):
        self.ensure_one()
        pay_term_lines = self.line_ids \
            .filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
        return [
            ('account_id', 'in', pay_term_lines.account_id.ids),
            ('parent_state', '=', 'posted'),
            ('partner_id', '=', self.partner_id.id),
            ('reconciled', '=', False),
            ('move_id', '=', self.move_id.id),
            '|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0),
        ]

    def _compute_total_remaining_amount(self):
        for payment in self:
            domain = payment._get_move_line_domain()
            move_lines = self.env['account.move.line'].search(domain)
            amount_residual_currency = 0
            for line in move_lines:
                amount_residual_currency += line.amount_residual
            payment.total_remaining_amount = abs(amount_residual_currency)

    def get_invoice_bill_move_lines(self):
        for payment in self:
            if payment.payment_type == "outbound":
                internal_type = 'payable'
                operator = '<'
            else:
                internal_type = 'receivable'
                operator = '>'

            domain = [('partner_id', '=', payment.partner_id.id), ('company_id', '=', payment.company_id.id),
                      ('parent_state', '=', 'posted'), ('account_id.internal_type', '=', internal_type)]
            if not self.company_id.enable_adjust_payment_multi_currency:
                domain += [('currency_id', '=', self.currency_id.id)]
        return domain

    def _compute_total_outstanding_balance(self):
        for payment in self:
            outstanding_balance = 0
            if payment.state == "posted":
                move_line_domain = payment.get_invoice_bill_move_lines()
                move_line_ids = self.env['account.move.line'].search(move_line_domain)
                outstanding_balance = abs(sum(move_line_ids.mapped('balance')))
            payment.outstanding_balance = outstanding_balance

    @api.depends("reconciled_invoices_count", "reconciled_bills_count", "opening_invoice_bill_ids_count")
    def _compute_invoice_bill_number(self):
        for payment in self:
            if payment.reconciled_invoice_ids:
                payment.invoice_bill_number = ', '.join(payment.reconciled_invoice_ids.mapped('name'))
            elif payment.reconciled_bill_ids:
                payment.invoice_bill_number = ', '.join(payment.reconciled_bill_ids.mapped('name'))
            elif payment.opening_invoice_bill_ids:
                payment.invoice_bill_number = ', '.join(payment.opening_invoice_bill_ids.mapped('name'))
            else:
                payment.invoice_bill_number = False

    total_remaining_amount = fields.Monetary(compute="_compute_total_remaining_amount")
    outstanding_balance = fields.Monetary(compute="_compute_total_outstanding_balance")
    place_of_collection = fields.Char(string="Place of Collection")
    opening_invoice_bill_ids = fields.Many2many('account.move', compute='_get_opening_invoice_bill_ids')
    opening_invoice_bill_ids_count = fields.Integer('Opening Invoice/Bill count', compute='_get_opening_invoice_bill_ids')
    invoice_bill_number = fields.Char('Invoice/Bill Number', compute="_compute_invoice_bill_number", store=True)
    tax_lock_date_message = fields.Char(related="move_id.tax_lock_date_message")

    def action_adjust_payment(self):
        self.ensure_one()
        if self.total_remaining_amount <= 0:
            raise UserError(_('No amount is available to adjust'))
        context = self._context.copy()
        context.update({
            'default_partner_id': self.partner_id.id,
            'default_remaining_amount_signed': self.total_remaining_amount,
            'default_payment_id': self.id
        })
        return {
            'name': 'Adjust Payment',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'adjust.payment.wizard',
            'context': context,
        }

    def _adjust_payment(self, invoice_data):
        self.ensure_one()
        if not invoice_data:
            raise ValidationError(_("Nothing to process!"))
        account_move_line_obj = self.env['account.move.line']
        move_lines = account_move_line_obj.search(self._get_move_line_domain())
        if move_lines:
            move_line = move_lines[0]
            for data in invoice_data:
                if not move_lines.reconciled:
                    move_id = data.get('move_id')
                    amount = data.get('amount')
                    currency_amount = self.company_currency_id._convert(amount, self.currency_id, self.company_id, move_id.date)
                    if data.get('move_line_id'):
                        account_move_line_obj = data.get('move_line_id') + move_line
                    move_id = move_id.with_context(
                        custom_adjust_flow=True,
                        adjusted_amount=amount,
                        adjusted_currency_amount=currency_amount,
                        adjusted_currency=self.company_currency_id,
                        partner_id=self.partner_id.id,
                        no_exchange_difference=True,
                        reconcile_move_lines=account_move_line_obj,
                        move_id=move_id,
                    )
                    move_id.js_assign_outstanding_line(move_line.id)

    def action_print_receipt(self):
        return self.env.ref('account.action_report_payment_receipt').report_action(self)

    def get_opening_moves_total(self, move_id):
        opening_move_lines = move_id.line_ids.filtered(lambda line: line.partner_id.id == self.partner_id.id and line.account_id.user_type_id.type in ['receivable', 'payable'])
        opening_move_total = abs(sum(opening_move_lines.mapped('amount_currency')))
        opening_move_total_due = abs(sum(opening_move_lines.mapped('amount_residual_currency')))

        return {'opening_move_total': opening_move_total, 'opening_move_total_due': opening_move_total_due}

    @api.depends('move_id.line_ids.matched_debit_ids', 'move_id.line_ids.matched_credit_ids')
    def _get_opening_invoice_bill_ids(self):
        ''' Retrieve the opening balance invoices/bill reconciled to the payments through the reconciliation (
        account.partial.reconcile).'''

        # Setting Default for all records
        self.opening_invoice_bill_ids = self.opening_invoice_bill_ids_count = False

        for rec in self.filtered(lambda line: line.ids):
            self.env['account.move'].flush()
            self.env['account.move.line'].flush()
            self.env['account.partial.reconcile'].flush()

            self._cr.execute('''
                SELECT
                    payment.id,
                    ARRAY_AGG(DISTINCT invoice.id) AS invoice_ids,
                    invoice.move_type
                FROM account_payment payment
                JOIN account_move move ON move.id = payment.move_id
                JOIN account_move_line line ON line.move_id = move.id
                JOIN account_partial_reconcile part ON
                    part.debit_move_id = line.id
                    OR
                    part.credit_move_id = line.id
                JOIN account_move_line counterpart_line ON
                    part.debit_move_id = counterpart_line.id
                    OR
                    part.credit_move_id = counterpart_line.id
                JOIN account_move invoice ON invoice.id = counterpart_line.move_id
                JOIN account_account account ON account.id = line.account_id
                WHERE account.internal_type IN ('receivable', 'payable')
                    AND payment.id IN %(payment_ids)s
                    AND line.id != counterpart_line.id
                    AND invoice.move_type = ('entry')
                GROUP BY payment.id, invoice.move_type
            ''', {
                'payment_ids': tuple(rec.ids)
            })
            query_res = self._cr.dictfetchall()
            for res in query_res:
                rec.opening_invoice_bill_ids += self.env['account.move'].browse(res.get('invoice_ids', []))
                rec.opening_invoice_bill_ids_count = len(res.get('invoice_ids', []))

    def button_open_opening_invoice_bill_ids(self):
        self.ensure_one()
        if not self.opening_invoice_bill_ids:
            return
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_journal_line")
        action['context'] = {'default_move_type': 'entry', 'create': 0}

        if len(self.opening_invoice_bill_ids) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = self.opening_invoice_bill_ids.id
        else:
            action['domain'] = [('id', 'in', self.opening_invoice_bill_ids.ids)]
        return action

    def action_post(self):
        super().action_post()
        for payment in self:
            move = payment.move_id
            affects_tax_report = move._affect_tax_report()
            lock_dates = move._get_violated_lock_dates(move.date, affects_tax_report)
            if lock_dates:
                payment.date = move._get_accounting_date(move.invoice_date or move.date, affects_tax_report)
