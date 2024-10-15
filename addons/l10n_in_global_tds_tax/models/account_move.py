# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    tds_tax_id = fields.Many2one('account.tax', string='TDS Tax', copy=False, domain=lambda self: [('type_tax_use', '=', 'purchase'),
                                                                                                   ('tax_group_id', '=', self.env.ref('l10n_in_tds_tcs.tds_group').id)])
    global_tds_tax_total_amount = fields.Monetary(string='Total TDS', store=True, readonly=True, compute='cal_move_global_tds_tax_amount')
    tds_tax_misc_move_id = fields.Many2one('account.move', string='TDS Tax Misc Move', copy=False)

    @api.depends('tds_tax_id', 'amount_untaxed', 'invoice_line_ids.tax_ids')
    def cal_move_global_tds_tax_amount(self):
        for rec in self:
            tds_tax_price = 0.00
            if not rec.check_move_lines_tds_tax():
                taxes = rec.tds_tax_id.compute_all(rec.amount_untaxed, rec.currency_id, partner=rec.partner_id)
                tds_tax_price = abs(sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])))
            rec.global_tds_tax_total_amount = tds_tax_price

    def action_global_tds_tax_apply(self):
        if self.check_move_lines_tds_tax():
            raise UserError(_("You can't club global TDS and invoice line tds tax on same bill."))
        return {
            'name': _('TDS Tax Apply'),
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.account.global.tds.tax',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_account_move_id': self.id}
        }

    def check_move_lines_tds_tax(self):
        self.ensure_one()
        tds_group_id = self.env.ref('l10n_in_tds_tcs.tds_group')
        if self.invoice_line_ids and any(tds_group_id in line.tax_ids.mapped('tax_group_id') for line in self.invoice_line_ids):
            return True
        return False

    def action_create_global_tds_tax_entry(self):
        self.ensure_one()
        if not self.tds_tax_id:
            return
        if self.check_move_lines_tds_tax():
            raise UserError(_("You can't club global TDS and invoice line tds tax on same bill."))
        tds_tax_move_id = self._create_tds_tax_move()
        tds_tax_move_id.action_post()
        partner_account = self.partner_account()
        move_line = self.line_ids.filtered(lambda line: line.account_id.id == partner_account)
        move_line += tds_tax_move_id.line_ids.filtered(lambda line: line.account_id.id == partner_account)
        move_line.reconcile()

    def _create_tds_tax_move(self):
        self.ensure_one()
        taxes = self.tds_tax_id.compute_all(self.amount_untaxed, self.currency_id, 1.0)['taxes']
        account_id = taxes[0]['account_id']
        if not account_id:
            raise UserError(_("Please configured account on TDS Tax."))
        journal_id = self._search_default_journal(['general'])
        if not journal_id:
            raise UserError(_("Please configured Miscellaneous type journal."))
        tds_tax_move_id = self.env['account.move'].create({
            'move_type': 'entry',
            'invoice_date': self.invoice_date,
            'journal_id': journal_id.id,
            'currency_id': self.currency_id.id,
            'line_ids': self.prepare_tds_tax_move_lines(account_id),
        })
        self.tds_tax_misc_move_id = tds_tax_move_id.id
        return tds_tax_move_id

    def prepare_tds_tax_move_lines(self, account_id):
        self.ensure_one()
        vals = [(0, 0, self.prepare_tds_tax_debit_move_line(account_id)), (0, 0, self.prepare_tds_tax_credit_move_line(account_id))]
        return vals

    def prepare_tds_tax_debit_move_line(self, account_id):
        account_id = account_id if self.move_type == 'in_refund' else self.partner_account()
        return {
            'name': self.name,
            'account_id': account_id,
            'partner_id': self.partner_id.id,
            'debit': self.global_tds_tax_total_amount,
            'quantity': 1,
            'currency_id': self.currency_id.id
        }

    def prepare_tds_tax_credit_move_line(self, account_id):
        account_id = account_id if self.move_type == 'in_invoice' else self.partner_account()
        return {
            'name': self.name,
            'account_id': account_id,
            'partner_id': self.partner_id.id,
            'credit': self.global_tds_tax_total_amount,
            'quantity': 1,
            'currency_id': self.currency_id.id
        }

    def partner_account(self):
        pay_account = self.partner_id.property_account_payable_id.id
        if self.is_purchase_document(include_receipts=True) and self.partner_id:
            pay_account = self.partner_id.commercial_partner_id.property_account_payable_id.id
        return pay_account

    def button_cancel(self):
        super().button_cancel()
        self.write({'tds_tax_id': False})

    def reset_button_draft(self):
        super().reset_button_draft()
        if self.tds_tax_misc_move_id:
            self.create_tds_tax_misc_reversal_entry()

    def create_tds_tax_misc_reversal_entry(self):
        move_reversal = self.env['account.move.reversal']\
            .with_context(active_model="account.move", active_ids=self.tds_tax_misc_move_id.ids).create({
                'date': fields.Date.today(),
                'refund_method': 'cancel',
                'journal_id': self.tds_tax_misc_move_id.journal_id.id,
            })
        move_reversal.reverse_moves()
        self.write({'tds_tax_misc_move_id': False})
