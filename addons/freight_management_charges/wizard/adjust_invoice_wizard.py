
from odoo import models, fields, api, _
from odoo.addons.account.models.account_move import PAYMENT_STATE_SELECTION
from odoo.exceptions import ValidationError


class AdjustInvoiceWizard(models.TransientModel):
    _name = 'adjust.invoice.wizard'
    _description = 'Adjust Invoice Wizard'

    credit_move_id = fields.Many2one('account.move', required=True)
    currency_id = fields.Many2one('res.currency', related='credit_move_id.currency_id', store=True)
    balance_amount = fields.Monetary(string='Balance Amount')
    multi_select_option = fields.Boolean(string='Multi Select')
    line_ids = fields.One2many('adjust.invoice.wizard.line', 'adjust_invoice_wizard_id')
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True,
                                          related='credit_move_id.company_currency_id')

    @api.onchange('multi_select_option')
    def _onchange_multi_select_option(self):
        if self.multi_select_option:
            self.line_ids.is_checked = True
        else:
            self.line_ids.is_checked = False

    def action_adjust_invoice(self):
        self.ensure_one()
        self._check_balance_amount_validation()
        line_ids = self.line_ids.filtered(lambda line: line.is_checked)
        for line in line_ids:
            move_lines = self.env['account.move.line'].search(line.move_id._get_invoice_move_line_domain())
            if move_lines:
                move_line_id = move_lines[0]
                if not move_line_id.reconciled:
                    move_id = self.credit_move_id.with_context(
                        custom_adjust_flow=True,
                        adjusted_amount=line.amount_residual_signed,
                        adjusted_currency_amount=line.amount_residual_signed,
                        adjusted_currency=self.currency_id,
                        partner_id=self.credit_move_id.partner_id.id,
                        no_exchange_difference=True,
                    )
                    if not move_id.reversed_entry_id:
                        move_id.reversed_entry_id = move_line_id.move_id.id
                    move_id.js_assign_outstanding_line(move_line_id.id)

    def _check_balance_amount_validation(self):
        line_ids = self.line_ids.filtered(lambda line: line.is_checked)
        if not line_ids:
            raise ValidationError(_("Nothing to adjust!"))
        amount_due_total = sum(line_ids.mapped('amount_residual_signed'))
        if amount_due_total > self.balance_amount:
            raise ValidationError(_("Total of Amount Due should not be greater than Balance Amount."))
        amount_due_validation = line_ids.filtered(lambda line: line.actual_amount_due < line.amount_residual_signed)
        if amount_due_validation:
            raise ValidationError(_("Amount due should not be greater than the actual amount due."))
        invalid_amount_due = line_ids.filtered(lambda line: line.amount_residual_signed <= 0)
        if invalid_amount_due:
            raise ValidationError(_("Amount due should be greater than 0."))


class AdjustInvoiceWizardLine(models.TransientModel):
    _name = 'adjust.invoice.wizard.line'
    _description = 'Adjust invoice Wizard Line'

    @api.depends('move_id', 'is_checked')
    def _compute_amount_residual_signed(self):
        for line in self:
            move_lines = line.move_id.line_ids.filtered(lambda move_line: move_line.partner_id.id == line.partner_id.id)
            source_amount_currency = 0
            for move_line in move_lines:
                source_amount_currency += move_line.amount_residual_currency
            source_amount_currency = abs(source_amount_currency)
            line.actual_amount_due = source_amount_currency
            line.amount_residual_signed = source_amount_currency if line.is_checked else 0.00

    adjust_invoice_wizard_id = fields.Many2one('adjust.invoice.wizard')
    move_id = fields.Many2one('account.move', string="Number")
    currency_id = fields.Many2one('res.currency', related='adjust_invoice_wizard_id.currency_id', store=True)
    partner_id = fields.Many2one('res.partner', string="Partner", related="move_id.partner_id")
    amount_total_signed = fields.Monetary('Total Signed')
    payment_state = fields.Selection(related="move_id.payment_state")
    state = fields.Selection(related="move_id.state")
    actual_amount_due = fields.Monetary("Actual Amount Due")
    amount_residual_signed = fields.Monetary("Amount Due", readonly=False, store=True,
                                             compute="_compute_amount_residual_signed",
                                             currency_field='currency_id')
    is_checked = fields.Boolean(string='Select')
    company_currency_id = fields.Many2one(related='adjust_invoice_wizard_id.company_currency_id', store=True)

    @api.onchange('amount_residual_signed', 'amount_total_signed')
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
