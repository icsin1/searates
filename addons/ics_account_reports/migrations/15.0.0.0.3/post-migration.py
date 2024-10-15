# -*- coding: utf-8 -*-
import json
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    def _modify_values(xml_id, values):
        record = env.ref(f'ics_account_reports.{xml_id}')
        if record:
            record.write(values)

    unaffected_earning = env.ref('account.data_unaffected_earnings')

    _modify_values('finance_report_balance_sheet_section_equity_curr_year_earnings_pnl', {
        'date_scope': 'from_fiscal_year',
        'computation_formula': '-sum',
        'data_domain': "[('account_id.user_type_id.internal_group', 'in', ['income', 'expense'])]"
    })

    _modify_values('finance_report_balance_sheet_section_equity_curr_year_earnings_alloc', {
        'date_scope': 'from_fiscal_year',
        'data_domain': json.dumps([('account_id.user_type_id', '=', unaffected_earning.id)])
    })

    _modify_values('finance_report_balance_sheet_section_equity_prev_year_earnings', {
        'computation_formula': '-sum - CURR_YEAR_EARNINGS',
        'date_scope': 'from_begin',
        'data_domain': json.dumps(['|', ('account_id.user_type_id.internal_group', 'in', ['income', 'expense']), ('account_id.user_type_id', '=', unaffected_earning.id)])
    })
