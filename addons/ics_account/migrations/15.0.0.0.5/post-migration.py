# -*- coding: utf-8 -*-

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for comp in env['res.company'].search([]):
        reconcile_entries = env['account.partial.reconcile'].search([
            ('company_id', '=', comp.id),
            '|',
            ('credit_currency_id', '!=', comp.currency_id.id),
            ('debit_currency_id', '!=', comp.currency_id.id),
        ])
        for reconcile_entry in reconcile_entries:
            reconcile_credit_amount_currency = round(reconcile_entry.credit_amount_currency, comp.currency_id.decimal_places)
            if comp.currency_id != reconcile_entry.credit_currency_id and reconcile_entry.amount == reconcile_credit_amount_currency:
                credit_move_id = reconcile_entry.credit_move_id.move_id
                credit_amount_currency = comp.currency_id._convert(
                    reconcile_entry.amount,
                    reconcile_entry.credit_currency_id,
                    reconcile_entry.company_id,
                    credit_move_id.date
                )
                reconcile_entry.write({'credit_amount_currency': credit_amount_currency})
                reconcile_entry.credit_move_id._compute_amount_residual()

            reconcile_debit_amount_currency = round(reconcile_entry.debit_amount_currency, comp.currency_id.decimal_places)
            if comp.currency_id != reconcile_entry.debit_currency_id and reconcile_entry.amount == reconcile_debit_amount_currency:
                debit_move_id = reconcile_entry.debit_move_id.move_id
                debit_amount_currency = reconcile_entry.company_currency_id._convert(
                    reconcile_entry.amount,
                    reconcile_entry.debit_currency_id,
                    reconcile_entry.company_id,
                    debit_move_id.date
                )
                reconcile_entry.write({'debit_amount_currency': debit_amount_currency})
                reconcile_entry.debit_move_id._compute_amount_residual()
