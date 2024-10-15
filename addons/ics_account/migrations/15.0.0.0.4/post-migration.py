# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def _fix_conversion_for_reconcile_entries(comp, reconcile_entries):
    """ Fixing issue which have created due to adjustment any currency amount to company currency
        Now converting those adjusted currency amount to perticular currency amount (debit/credit)
        Note that, here it will be checked only if debit and credit currency are different and company amount == debit or credit amount
    """
    for reconcile_entry in reconcile_entries:
        if reconcile_entry.debit_currency_id != reconcile_entry.credit_currency_id:

            # Checking if debit move currency is not equal to reconcile entry debit currency
            if reconcile_entry.amount == reconcile_entry.debit_amount_currency:
                debit_move_id = reconcile_entry.debit_move_id.move_id
                debit_amount_currency = reconcile_entry.company_currency_id._convert(
                    reconcile_entry.amount,  # Company Amount as Local Currency - From Currency Amount
                    reconcile_entry.debit_currency_id,  # Converting that amount to debit currency
                    reconcile_entry.company_id,
                    debit_move_id.date  # As per the debit move date
                )
                reconcile_entry.write({'debit_amount_currency': debit_amount_currency})

            # Checking if credit move currency is not equal to reconcile entry credit currency
            if reconcile_entry.amount == reconcile_entry.credit_amount_currency:
                credit_move_id = reconcile_entry.credit_move_id.move_id
                credit_amount_currency = reconcile_entry.company_currency_id._convert(
                    reconcile_entry.amount,  # Company Amount as Local Currency - From Currency Amount
                    reconcile_entry.credit_currency_id,  # Converting that amount to credit currency
                    reconcile_entry.company_id,
                    credit_move_id.date  # As per the credit move date
                )
                reconcile_entry.write({'credit_amount_currency': credit_amount_currency})


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for comp in env['res.company'].search([]):
        # Getting only those partial reconcile lines which are not same as company currency
        reconcile_entries = env['account.partial.reconcile'].search([
            ('company_id', '=', comp.id),
            '|',
            ('credit_currency_id', '!=', comp.currency_id.id),
            ('debit_currency_id', '!=', comp.currency_id.id)
        ])
        _fix_conversion_for_reconcile_entries(comp, reconcile_entries.with_company(comp))
