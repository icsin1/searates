# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    charge = env.ref('ics_account_reports.fm_report_general_ledger_column_amount_fcy')
    if charge:
        charge.write({'expression_label':'amount_currency'})
    expression_charge = env.ref('ics_account_reports.fm_report_general_ledger_amount_fcy')
    if expression_charge:
        expression_charge.write({'formula_expression': 'amount_currency', 'name': 'amount_currency', 'computation_engine': 'field'})
