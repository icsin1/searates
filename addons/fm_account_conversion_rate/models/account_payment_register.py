# -*- coding: utf-8 -*-

from odoo import models, api


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payment_vals_from_wizard(self):
        payment_vals = super()._create_payment_vals_from_wizard()
        move_id = self.line_ids.move_id[0]
        if move_id.currency_exchange_rate and move_id.currency_id.id == payment_vals.get('currency_id'):
            payment_vals['currency_exchange_rate'] = move_id.currency_exchange_rate
        return payment_vals

    def _create_payment_vals_from_batch(self, batch_result):
        batch_vals = super()._create_payment_vals_from_batch(batch_result)
        lines = batch_result['lines']
        if lines:
            move_id = lines.mapped('move_id')[0]
            if move_id.currency_exchange_rate:
                batch_vals['currency_exchange_rate'] = move_id.currency_exchange_rate
        return batch_vals

    @api.model
    def _get_line_batch_key(self, line):
        batch_key = super()._get_line_batch_key(line)
        if line.move_id.currency_exchange_rate:
            batch_key['currency_exchange_rate'] = line.move_id.currency_exchange_rate
        return batch_key

    def _reconcile_payments(self, to_process, edit_mode=False):
        domain = [
            ('parent_state', '=', 'posted'),
            ('account_internal_type', 'in', ('receivable', 'payable')),
            ('reconciled', '=', False),
        ]
        for vals in to_process:
            payment_lines = vals['payment'].line_ids.filtered_domain(domain)
            lines = vals['to_reconcile']
            currency_exchange_rate = vals['create_vals'].get('currency_exchange_rate', 0.00)
            for account in payment_lines.account_id:
                (payment_lines + lines).with_context(
                    currency_exchange_rate=currency_exchange_rate
                ).filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)]).reconcile()
