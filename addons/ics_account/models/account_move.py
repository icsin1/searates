from datetime import date, timedelta

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from odoo.tools import date_utils
from odoo.tools.misc import format_date


READONLY_STAGE = {'draft': [('readonly', False)]}


class AccountMove(models.Model):
    _inherit = "account.move"

    # stored value stored in name before migration - 15.0.0.0.2
    old_name = fields.Char('Old System Generated Reference Number')

    allow_reference_number = fields.Boolean('Custom Reference Number', related='company_id.allow_reference_number', required=True)
    currency_exchange_rate = fields.Float('Ex.Rate', copy=False, digits='Currency Exchange Rate')
    po_number = fields.Char('PO Number', copy=False)
    invoice_terms_template_id = fields.Many2one('invoice.terms.template', string="Template",
                                                states=READONLY_STAGE, readonly=True)
    notes = fields.Html('Terms and conditions', states=READONLY_STAGE, readonly=True)
    label = fields.Char(help="Show Label in Financial Report.", copy=False, tracking=True, string="Label ")
    narration = fields.Text(string='Terms and Conditions',states=READONLY_STAGE, readonly=False, default='')

    def _get_move_display_name(self, show_ref=False):
        """ Helper to get the display name of an invoice depending of its type.
        :param show_ref:    A flag indicating of the display name must include or not the journal entry reference.
        :return:            A string representing the invoice.
        """
        self.ensure_one()
        name = ''
        if self.state == 'draft':
            name += {
                'out_invoice': _('Draft Invoice'),
                'out_refund': _('Draft Credit Note'),
                'in_invoice': _('Draft Bill'),
                'in_refund': _('Draft Vendor Credit Note'),
                'out_receipt': _('Draft Sales Receipt'),
                'in_receipt': _('Draft Purchase Receipt'),
                'entry': _('Draft Entry'),
            }[self.move_type]
            name += ' '
        if not self.name or self.name == '/':
            name += '(* %s)' % str(self.id)
        else:
            name += self.name
        return name + (show_ref and self.ref and ' (%s%s)' % (self.ref[:50], '...' if len(self.ref) > 50 else '') or '')

    @api.onchange('invoice_terms_template_id')
    def _onchange_invoice_terms_template_id(self):
        self.notes = False
        if self.invoice_terms_template_id:
            self.notes = self.invoice_terms_template_id.body_html

    def action_print_payment_receipt(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('ics_account.action_account_payments_print_receipts')
        move_payment_values = self._get_reconciled_info_JSON_values()
        payment_ids = list(map(lambda val: val.get('account_payment_id'), move_payment_values))
        action['domain'] = [('id', 'in', payment_ids)]
        action['context'] = {
            'create': 0,
            'edit': 0,
            'delete': 0,
            'select': 1,
        }
        action['target'] = 'new'
        return action

    def _recompute_dynamic_lines(self, recompute_all_taxes=False, recompute_tax_base_amount=False):
        return super(AccountMove, self.with_context(
            currency_exchange_rate=self.currency_exchange_rate
        ))._recompute_dynamic_lines(recompute_all_taxes, recompute_tax_base_amount)

    def preview_invoice(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': self.get_portal_url(),
        }

    def action_debit_reverse(self):
        action = self.action_reverse()

        if self.move_type == 'in_invoice':
            action['name'] = _('Debit Note')

        return action

    def get_opening_balance_reconciled_lines(self, payment_id):
        self.ensure_one()
        pay_term_lines = self.line_ids\
            .filtered(lambda line: line.account_internal_type in ('receivable', 'payable') and line.partner_id.id == payment_id.partner_id.id)
        invoice_partials = []

        for partial in pay_term_lines.matched_debit_ids:
            invoice_partials.append((partial, partial.credit_amount_currency, partial.debit_move_id))
        for partial in pay_term_lines.matched_credit_ids:
            invoice_partials.append((partial, partial.debit_amount_currency, partial.credit_move_id))

        return invoice_partials

    @api.onchange('name', 'highest_name')
    def _onchange_name_warning(self):
        # Forcing to ignore warning with sequence change as we are allowing different/manual numbers
        if not self.allow_reference_number:
            return super()._onchange_name_warning()

    def button_draft(self):
        if len(self) > 1:
            return self.reset_button_draft()

        context = self._context.copy()
        payment = False
        if self.payment_state in ['partial', 'paid', 'in_payment', 'reversed']:
            payment = True

        message = ''
        if self.move_type == 'out_invoice':
            message = 'The Payment/Credit note is attached to this invoice, do you want to Unreconcile?'
        elif self.move_type == 'in_invoice':
            message = 'The Payment/Debit note is attached to this bill, do you want to Unreconcile?'
        elif self.move_type == 'out_refund':
            message = 'The Payment/Invoice is attached to this credit note, do you want to Unreconcile?'
        elif self.move_type == 'in_refund':
            message = 'The Payment/Bill is attached to this debit note, do you want to Unreconcile?'

        if payment and message:
            context.update({
                'default_name': message,
                'current_move_id': self.id
            })
            return {
                'name': 'Reset To Draft',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'res_model': 'reset.to.draft.wizard',
                'context': context,
            }
        else:
            self.reset_button_draft()

    def reset_button_draft(self):
        res = super().button_draft()
        for move in self:
            move.line_ids.filtered(lambda x: x.name == move.payment_reference).write({'name': False})
            move.write({'payment_reference': False})
        return res

    def action_post(self):
        for move in self:
            move.check_unique_sequence_per_company()
        result = super(AccountMove, self).action_post()
        for inv in self.filtered(lambda move: not move.label and move.move_type != 'entry'):
            inv.label = inv.name
        return result

    def check_unique_sequence_per_company(self):
        if not self.allow_reference_number:
            return
        existing_moves = self.env['account.move'].search_count([
            ('company_id', '=', self.company_id.id),
            ('state', '=', 'posted'),
            ('name', '=', self.name)])
        if existing_moves:
            raise ValidationError(_('Posted journal entry must have an unique sequence number per company.\n'
                                    'Problematic numbers: %s\n') % self.name)

    @api.model
    def _get_invoice_in_payment_state(self):
        return 'in_payment'

    def _get_accounting_date(self, invoice_date, has_tax):
        """Get correct accounting date for previous periods, taking tax lock date into account.

        When registering an invoice in the past, we still want the sequence to be increasing.
        We then take the last day of the period, depending on the sequence format.
        If there is a tax lock date and there are taxes involved, we register the invoice at the
        last date of the first open period.

        :param invoice_date (datetime.date): The invoice date
        :param has_tax (bool): Iff any taxes are involved in the lines of the invoice
        :return (datetime.date):
        """
        lock_dates = self._get_violated_lock_dates(invoice_date, has_tax)
        today = fields.Date.context_today(self)
        highest_name = self.highest_name or self._get_last_sequence(relaxed=True, lock=False)
        number_reset = self._deduce_sequence_number_reset(highest_name)
        if lock_dates:
            invoice_date = lock_dates[-1][0] + timedelta(days=1)
        if self.is_sale_document(include_receipts=True):
            if lock_dates:
                if not highest_name or number_reset == 'month':
                    return min(today, invoice_date)
                elif number_reset == 'year':
                    return min(today, date_utils.end_of(invoice_date, 'year'))
        else:
            if not highest_name or number_reset == 'month':
                if (today.year, today.month) > (invoice_date.year, invoice_date.month):
                    return invoice_date
                else:
                    return invoice_date
            elif number_reset == 'year':
                if today.year > invoice_date.year:
                    return date(invoice_date.year, 12, 31)
                else:
                    return max(invoice_date, today)
        return invoice_date

    def _compute_tax_lock_date_message(self):
        for move in self:
            # invoice_date = move.invoice_date or fields.Date.context_today(move)
            accounting_date = move.date or fields.Date.context_today(move)
            affects_tax_report = move._affect_tax_report()
            lock_dates = move._get_violated_lock_dates(accounting_date, affects_tax_report)
            if lock_dates:
                accounting_date = move._get_accounting_date(accounting_date, affects_tax_report)
                lock_date, lock_type = lock_dates[-1]
                tax_lock_date_message = _(
                    "The accounting date being set prior to the %(lock_type)s lock date %(lock_date)s,"
                    " it will be changed to %(accounting_date)s upon posting.",
                    lock_type=lock_type,
                    lock_date=format_date(move.env, lock_date),
                    accounting_date=format_date(move.env, accounting_date))
                for lock_date, lock_type in lock_dates[:-1]:
                    tax_lock_date_message += _(" The %(lock_type)s lock date is set on %(lock_date)s.",
                                               lock_type=lock_type,
                                               lock_date=format_date(move.env, lock_date))
                move.tax_lock_date_message = tax_lock_date_message
            else:
                move.tax_lock_date_message = False


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    invoice_date = fields.Date(related='move_id.invoice_date', string='Invoice Date', store=True)

    def _custom_prepare_reconciliation_partials(self):
        ''' RE WRITTEN THE CODE TO SUPPORT PARTIAL ADJUSTMENT FROM PAYMENT ON INVOICE
            Why Re-write?

            By default odoo's method _prepare_reconciliation_partials() does not allow in-between patch to support this
            We have force override in chase we are adjusting payment from payment screen.
        '''
        def fix_remaining_cent(currency, abs_residual, partial_amount):
            if abs_residual - currency.rounding <= partial_amount <= abs_residual + currency.rounding:
                return abs_residual
            else:
                return partial_amount

        debit_lines = iter(self.filtered(lambda line: line.balance > 0.0 or line.amount_currency > 0.0 and not line.reconciled))
        credit_lines = iter(self.filtered(lambda line: line.balance < 0.0 or line.amount_currency < 0.0 and not line.reconciled))
        void_lines = iter(self.filtered(lambda line: not line.balance and not line.amount_currency and not line.reconciled))
        debit_line = None
        credit_line = None

        debit_amount_residual = 0.0
        debit_amount_residual_currency = 0.0
        credit_amount_residual = 0.0
        credit_amount_residual_currency = 0.0
        debit_line_currency = None
        credit_line_currency = None

        partials_vals_list = []

        # Applying patch for adjusted amount and currency
        adjusted_amount = self._context.get('adjusted_amount', None)
        adjusted_currency_amount = self._context.get('adjusted_currency_amount', None)
        adjust_currency = self._context.get('adjusted_currency', None)
        exchange_rate = False
        move_id = self._context.get('move_id', False)

        while True:
            if not debit_line:
                debit_line = next(debit_lines, None) or next(void_lines, None)
                if not debit_line:
                    break
                if debit_line.move_id.move_type != 'entry':
                    exchange_rate = debit_line.move_id.currency_exchange_rate
            if not credit_line:
                credit_line = next(void_lines, None) or next(credit_lines, None)
                if not credit_line:
                    break
                if credit_line.move_id.move_type != 'entry':
                    exchange_rate = credit_line.move_id.currency_exchange_rate
            # Changing amount and currency based on partial adjusted amount and payment currency
            debit_amount_residual = adjusted_amount or debit_line.amount_residual_currency
            debit_line_currency = (adjust_currency == debit_line.currency_id and adjust_currency) or debit_line.currency_id
            if debit_line_currency:
                # Getting company currency based amount
                adjust_debit_currency = (adjust_currency and adjust_currency) or debit_line.company_currency_id
                adjusted_currency_amount = adjust_debit_currency.with_context(currency_exchange_rate=exchange_rate)._convert(
                    adjusted_amount, debit_line.currency_id, debit_line.company_id, move_id and move_id.date or fields.Date.today())
                debit_amount_residual_currency = adjusted_currency_amount
            else:
                debit_amount_residual_currency = debit_amount_residual
                debit_line_currency = debit_line.company_currency_id

            # Changing amount and currency based on partial adjusted amount and payment currency
            credit_amount_residual = -adjusted_amount or credit_line.amount_residual
            credit_line_currency = (adjust_currency == credit_line.currency_id and adjust_currency) or credit_line.currency_id
            if credit_line_currency:
                # Getting company currency based amount
                adjust_credit_currency = (adjust_currency and adjust_currency) or credit_line.company_currency_id
                adjusted_currency_amount = adjust_credit_currency.with_context(currency_exchange_rate=exchange_rate)._convert(
                    adjusted_amount, credit_line.currency_id, credit_line.company_id, move_id and move_id.date or fields.Date.today())
                credit_amount_residual_currency = -adjusted_currency_amount
            else:
                credit_amount_residual_currency = credit_amount_residual
                credit_line_currency = credit_line.company_currency_id
            min_amount_residual = min(debit_amount_residual, -credit_amount_residual)
            if debit_line_currency == credit_line_currency:
                # Reconcile on the same currency.

                min_amount_residual_currency = min(debit_amount_residual_currency, -credit_amount_residual_currency)
                min_debit_amount_residual_currency = min_amount_residual_currency
                min_credit_amount_residual_currency = min_amount_residual_currency

            else:
                # Reconcile on the company's currency.

                min_debit_amount_residual_currency = credit_line.company_currency_id.with_context(currency_exchange_rate=exchange_rate)._convert(
                    min_amount_residual,
                    debit_line.currency_id,
                    credit_line.company_id,
                    move_id and move_id.date or credit_line.date,
                )
                min_debit_amount_residual_currency = fix_remaining_cent(
                    debit_line.currency_id,
                    debit_amount_residual_currency,
                    min_debit_amount_residual_currency,
                )
                min_credit_amount_residual_currency = debit_line.company_currency_id.with_context(currency_exchange_rate=exchange_rate)._convert(
                    min_amount_residual,
                    credit_line.currency_id,
                    debit_line.company_id,
                    move_id and move_id.date or debit_line.date,
                )
                min_credit_amount_residual_currency = fix_remaining_cent(
                    credit_line.currency_id,
                    -credit_amount_residual_currency,
                    min_credit_amount_residual_currency,
                )

            debit_amount_residual -= min_amount_residual
            debit_amount_residual_currency -= min_debit_amount_residual_currency
            credit_amount_residual += min_amount_residual
            credit_amount_residual_currency += min_credit_amount_residual_currency

            partials_vals_list.append({
                'amount': min_amount_residual,
                'debit_amount_currency': min_debit_amount_residual_currency,
                'credit_amount_currency': min_credit_amount_residual_currency,
                'debit_move_id': debit_line.id,
                'credit_move_id': credit_line.id,
            })

            has_debit_residual_left = not debit_line.company_currency_id.is_zero(debit_amount_residual) and debit_amount_residual > 0.0
            has_credit_residual_left = not credit_line.company_currency_id.is_zero(credit_amount_residual) and credit_amount_residual < 0.0
            has_debit_residual_curr_left = not debit_line_currency.is_zero(debit_amount_residual_currency) and debit_amount_residual_currency > 0.0
            has_credit_residual_curr_left = not credit_line_currency.is_zero(credit_amount_residual_currency) and credit_amount_residual_currency < 0.0

            if debit_line_currency == credit_line_currency:
                # The debit line is now fully reconciled because:
                # - either amount_residual & amount_residual_currency are at 0.
                # - either the credit_line is not an exchange difference one.
                if not has_debit_residual_curr_left and (has_credit_residual_curr_left or not has_debit_residual_left):
                    debit_line = None

                # The credit line is now fully reconciled because:
                # - either amount_residual & amount_residual_currency are at 0.
                # - either the debit is not an exchange difference one.
                if not has_credit_residual_curr_left and (has_debit_residual_curr_left or not has_credit_residual_left):
                    credit_line = None

            else:
                # The debit line is now fully reconciled since amount_residual is 0.
                if not has_debit_residual_left:
                    debit_line = None

                # The credit line is now fully reconciled since amount_residual is 0.
                if not has_credit_residual_left:
                    credit_line = None

        return partials_vals_list

    def _prepare_reconciliation_partials(self):
        """
        override to adjust custom amount from account.payment
        """
        if self._context.get('custom_adjust_flow'):
            if self.env.context.get('reconcile_move_lines'):
                self = self.env.context.get('reconcile_move_lines').with_context(self.env.context)
            return self._custom_prepare_reconciliation_partials()
        return super()._prepare_reconciliation_partials()


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    allow_reference_number = fields.Boolean('Custom Reference Number', related='move_id.company_id.allow_reference_number', required=True)

    def action_draft(self):
        super().action_draft()
        self.move_id.name = '/'

    def action_post(self):
        for payment in self:
            payment.move_id.check_unique_sequence_per_company()
        return super().action_post()
