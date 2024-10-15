
from odoo import models, fields, api, _


class WizBalanceConfirmationReport(models.Model):
    _name = 'wiz.balance.confirmation.report'
    _description = 'Balance Confirmation Report'

    date = fields.Date(required=True)
    partner_id = fields.Many2one('res.partner', required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    other_currency_id = fields.Many2one('res.currency')
    due_amount = fields.Monetary(currency_field='currency_id')
    due_amount_other_currency = fields.Monetary(currency_field='other_currency_id')

    def action_partner_balance_info(self):
        return self.env.ref('ics_account_reports.action_balance_confirmation_report').report_action(self)

    @api.onchange('partner_id', 'date')
    def _onchange_partner_id(self):
        domain = [('company_id', '=', self.company_id.id), ('date', '<=', self.date), ('parent_state', '=', 'posted'),
                  ('account_id.internal_type', 'in', ['receivable', 'payable']), ('partner_id', '=', self.partner_id.id)]
        move_line_ids = self.env['account.move.line'].search(domain)

        amount_residual_currency = sum(move_line_ids.mapped('balance'))
        move_ids = move_line_ids.mapped('move_id')
        foreign_currency_ids = move_ids.filtered(lambda l: not l.payment_id and l.currency_id.id != self.currency_id.id).mapped('currency_id')
        company_currency_moves = move_ids.filtered(lambda l: not l.payment_id and l.currency_id.id == self.currency_id.id)

        other_currency_id = False
        amount_currency = 0.00

        if not company_currency_moves and len(foreign_currency_ids) == 1:
            other_currency_id = foreign_currency_ids.filtered(lambda l: l.id != self.currency_id.id).id
            amount_currency = sum(move_line_ids.mapped('amount_currency'))

        self.due_amount = amount_residual_currency
        self.due_amount_other_currency = amount_currency
        self.other_currency_id = other_currency_id
