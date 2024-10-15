
from odoo import models, fields, Command, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    withholding_tax_id = fields.Many2one('account.tax')

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        self.ensure_one()
        line_vals_list = super()._prepare_move_line_default_vals(write_off_line_vals)
        if line_vals_list and self.withholding_tax_id and self.partner_type == 'supplier' and not self.is_internal_transfer:
            withholding_tax_line_vals = self.prepare_withholding_tax_vals()
            liquidity_line = line_vals_list[0]
            liquidity_line['amount_currency'] -= withholding_tax_line_vals['amount_currency']
            liquidity_line['debit'] -= withholding_tax_line_vals['debit']
            liquidity_line['credit'] -= withholding_tax_line_vals['credit']
            line_vals_list.append(withholding_tax_line_vals)

        return line_vals_list

    def prepare_withholding_tax_vals(self):
        payment_display_name = self._prepare_payment_display_name()
        default_line_name = self.env['account.move.line']._get_default_line_name(payment_display_name['%s-%s' % (self.payment_type, self.partner_type)],
                                                                                 self.amount, self.currency_id, self.date, partner=self.partner_id)
        taxes = self.withholding_tax_id.compute_all(self.amount, self.currency_id, 1.0)['taxes']
        tax_amount = abs(sum(t.get('amount', 0.0) for t in taxes))
        account_id = taxes[0]['account_id']
        if not account_id:
            raise UserError(_('Please configured account in %s.') % (self.withholding_tax_id.name))

        withholding_tax_amount_currency = -tax_amount
        withholding_tax_amount_balance = self.currency_id._convert(
            withholding_tax_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.date
        )
        return {
            'name': self.payment_reference or default_line_name,
            'date_maturity': self.date,
            'amount_currency': withholding_tax_amount_currency,
            'currency_id': self.currency_id.id,
            'debit': withholding_tax_amount_balance if withholding_tax_amount_balance > 0.0 else 0.0,
            'credit': -withholding_tax_amount_balance if withholding_tax_amount_balance < 0.0 else 0.0,
            'partner_id': self.partner_id.id,
            'account_id': account_id,
            'withholding_tax_line': True
            }

    def _synchronize_to_moves(self, changed_fields):
        ''' If we change a payment with withholdings, delete all withholding lines as the synchronization mechanism is not
        implemented yet
        '''
        for pay in self:
            pay.line_ids.filtered(lambda ml: ml.withholding_tax_line).with_context(check_move_validity=False).unlink()

        super()._synchronize_to_moves(changed_fields)
        if self._context.get('skip_account_move_synchronization'):
            return

        if len(changed_fields) == 1 and 'withholding_tax_id' not in changed_fields:
            return

        if len(changed_fields) == 1 and 'withholding_tax_id' in changed_fields:
            for pay in self.with_context(skip_account_move_synchronization=True):
                liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()
                if liquidity_lines and counterpart_lines and writeoff_lines:
                    counterpart_amount = sum(counterpart_lines.mapped('amount_currency'))
                    writeoff_amount = sum(writeoff_lines.mapped('amount_currency'))

                    # To be consistent with the payment_difference made in account.payment.register,
                    # 'writeoff_amount' needs to be signed regarding the 'amount' field before the write.
                    # Since the write is already done at this point, we need to base the computation on accounting values.
                    if (counterpart_amount > 0.0) == (writeoff_amount > 0.0):
                        sign = -1
                    else:
                        sign = 1
                    writeoff_amount = abs(writeoff_amount) * sign

                    write_off_line_vals = {
                        'name': writeoff_lines[0].name,
                        'amount': writeoff_amount,
                        'account_id': writeoff_lines[0].account_id.id,
                    }
                else:
                    write_off_line_vals = {}

                line_vals_list = pay._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)
                line_ids_commands = [
                    Command.update(liquidity_lines.id, line_vals_list[0]) if liquidity_lines else Command.create(line_vals_list[0]),
                    Command.update(counterpart_lines.id, line_vals_list[1]) if counterpart_lines else Command.create(line_vals_list[1])
                ]

                for line in writeoff_lines:
                    line_ids_commands.append((2, line.id))

                for extra_line_vals in line_vals_list[2:]:
                    line_ids_commands.append((0, 0, extra_line_vals))

                # Update the existing journal items.
                # If dealing with multiple write-off lines, they are dropped and a new one is generated.

                pay.move_id.write({
                    'partner_id': pay.partner_id.id,
                    'currency_id': pay.currency_id.id,
                    'partner_bank_id': pay.partner_bank_id.id,
                    'line_ids': line_ids_commands,
                })

    def _synchronize_from_moves(self, changed_fields):
        if self.withholding_tax_id:
            return
        super()._synchronize_from_moves(changed_fields)
