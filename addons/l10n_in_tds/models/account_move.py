# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    compute_tds = fields.Boolean(default=True, copy=False, string="Compute TDS",
                                 readonly=True, states={'draft': [('readonly', False)]})
    total_tds_amount = fields.Monetary(string='Total TDS', store=True, readonly=True,
                                       tracking=True, compute='cal_move_tds_amount')
    company_calculate_tds = fields.Boolean(related='company_id.calculate_tds', store=True)

    @api.depends('invoice_line_ids', 'invoice_line_ids.tds_amount',
                 'invoice_line_ids.account_tds_rate_id',
                 'invoice_line_ids.price_subtotal',
                 'compute_tds')
    def cal_move_tds_amount(self):
        for rec in self:
            rec.total_tds_amount = sum(rec.invoice_line_ids.mapped('tds_amount'))

    @api.onchange('company_calculate_tds')
    def _onchange_company_calculate_tds(self):
        self.compute_tds = self.company_calculate_tds

    @api.onchange('compute_tds', 'total_tds_amount')
    def _onchange_total_tds_amount(self):
        self._recompute_dynamic_lines()

    def _recompute_dynamic_lines(self, recompute_all_taxes=False, recompute_tax_base_amount=False):
        res = super()._recompute_dynamic_lines(recompute_all_taxes, recompute_tax_base_amount)
        for invoice in self:
            if invoice.is_invoice(include_receipts=True):
                invoice._recompute_tds_amount_lines()

                # Compute cash rounding.
                invoice._recompute_cash_rounding_lines()
                # Compute payment terms.
                invoice._recompute_payment_terms_lines()

                # Only synchronize one2many in onchange.
                if invoice != invoice._origin:
                    invoice.invoice_line_ids = invoice.line_ids.filtered(
                        lambda line: not line.exclude_from_invoice_tab)
        return res

    def _recompute_tds_amount_lines(self):
        ''' Compute the dynamic global TDS amount lines of the journal entry.'''
        self.ensure_one()
        self = self.with_company(self.company_id)
        in_draft_mode = self != self._origin
        account_tds_lines = self.env['account.move.line']

        def _get_tds_amount(self, tds_amount):
            if not self.compute_tds or not self.company_calculate_tds:
                return 0.00, 0.00
            sign = 1 if self.is_inbound() else -1
            tds_amount *= sign
            if self.currency_id == self.company_id.currency_id:
                tds_amount_currency = tds_amount
            else:
                tds_amount_currency = tds_amount
                tds_amount = self.currency_id._convert(
                    tds_amount_currency, self.company_id.currency_id, self.company_id, self.date)

            return tds_amount, tds_amount_currency

        def _get_tds_account(self):
            if self.move_type in ('out_invoice', 'in_refund'):
                tds_account_id = self.company_id.tds_receivable_account_id
            if self.move_type in ('in_invoice', 'out_refund'):
                tds_account_id = self.company_id.tds_payable_account_id

            if not tds_account_id:
                raise UserError(_("TDS Account is not found. please configure account in accounting configuration settings."))

            return tds_account_id

        def _compute_apply_tds_amount_line(self, existing_tds_lines, tds_account_id, balance, tds_amount_currency):
            new_account_tds_lines = self.env['account.move.line']
            if existing_tds_lines:
                candidate = existing_tds_lines[0]
                candidate.update({
                    'amount_currency': tds_amount_currency,
                    'debit': balance > 0.0 and balance or 0.0,
                    'credit': balance < 0.0 and -balance or 0.0,
                    'account_id': tds_account_id.id
                })
            else:
                create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
                candidate = create_method({
                    'name': 'TDS Amount',
                    'debit': balance > 0.0 and balance or 0.0,
                    'credit': balance < 0.0 and -balance or 0.0,
                    'quantity': 1.0,
                    'amount_currency': tds_amount_currency,
                    'date_maturity': self.invoice_date,
                    'move_id': self.id,
                    'currency_id': self.currency_id.id,
                    'account_id': tds_account_id.id,
                    'partner_id': self.commercial_partner_id.id,
                    'exclude_from_invoice_tab': True,
                    'is_tds_line': True
                })
            new_account_tds_lines += candidate
            if in_draft_mode:
                candidate.update(candidate._get_fields_onchange_balance(force_computation=True))
            return new_account_tds_lines

        def _compute_update_partner_amount(self, existing_partner_lines, tds_amount, tds_amount_currency):
            if not existing_partner_lines:
                return

            sign = 1 if self.is_inbound() else -1
            currency = self.currency_id
            tds_amount *= sign

            others_lines = self.line_ids.filtered(lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable') and not line.is_tds_line)
            candidate = existing_partner_lines[-1]
            candidate_amount = abs(candidate.amount_currency)
            company_currency_id = (self.company_id or self.env.company).currency_id
            total_balance = abs(sum(others_lines.mapped(lambda l: company_currency_id.round(l.balance))))
            candidate_balance = company_currency_id.round(candidate.balance) * sign

            if len(existing_partner_lines) == 1:
                partner_diff_balance = (total_balance - tds_amount)
            else:
                partner_diff_balance = candidate_balance

            diff_balance = candidate_amount
            if not tds_amount and currency and currency.is_zero(diff_balance):
                return

            diff_balance *= sign
            partner_diff_balance *= sign
            if diff_balance:
                candidate.update({
                    'amount_currency': diff_balance,
                    'debit': partner_diff_balance > 0.0 and partner_diff_balance or 0.0,
                    'credit': partner_diff_balance < 0.0 and -partner_diff_balance or 0.0,
                })
                if in_draft_mode:
                    candidate.update(candidate._get_fields_onchange_balance(force_computation=True))

        existing_tds_lines = self.line_ids.filtered(lambda line: line.is_tds_line)
        others_lines = self.line_ids.filtered(lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
        others_lines -= existing_tds_lines

        if not others_lines:
            self.line_ids -= existing_tds_lines
            return

        tds_amount, tds_amount_currency = _get_tds_amount(self, self.total_tds_amount)
        existing_partner_lines = self.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable') and not line.is_tds_line)
        _compute_update_partner_amount(self, existing_partner_lines, tds_amount, tds_amount_currency)

        if self.currency_id and self.currency_id.is_zero(tds_amount) and self.currency_id.is_zero(tds_amount_currency):
            self.line_ids -= existing_tds_lines
            return

        if self.company_calculate_tds and self.compute_tds:
            tds_account_id = _get_tds_account(self)
            account_tds_lines = _compute_apply_tds_amount_line(self, existing_tds_lines, tds_account_id, tds_amount, tds_amount_currency)

        self.line_ids -= existing_tds_lines - account_tds_lines

    def get_tds_groups_totals(self):
        tds_group_total = {}
        for invoice_line in self.line_ids.filtered(lambda l: l.account_tds_rate_id):
            tds_group_total.setdefault(invoice_line.account_tds_rate_id, {'tds_amount': 0.00, 'invoice_line_amount': 0.00})
            tds_group_total[invoice_line.account_tds_rate_id]['tds_amount'] += invoice_line.tds_amount
            tds_group_total[invoice_line.account_tds_rate_id]['invoice_line_amount'] += abs(invoice_line.amount_currency)

        return tds_group_total
