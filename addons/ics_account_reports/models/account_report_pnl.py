from odoo import models


class AccountReportPnL(models.Model):
    _inherit = 'account.move.line'

    def _get_pnl_report_data(self, domain=[], **kwargs):
        # income_lines = self.search([('account_id.user_type_id.internal_group', '=', 'income')] + domain)
        expense_lines = self.search([('account_id.user_type_id.internal_group', '=', 'expense')] + domain)

        income_value, income_lines = self._get_income_lines(domain, **kwargs)

        expense_value = sum(expense_lines.mapped('balance'))
        net_profit = income_value - expense_value

        lines = [
            {'lvl': 0, 'label': 'Income', 'id': 'income', 'values': {'2023': (income_value, self._format_currency(income_value))}, 'children': income_lines},
            {'lvl': 0, 'label': 'Expenses', 'id': 'expense', 'values': {'2023': (expense_value, self._format_currency(expense_value))}, 'children': []},
            {'lvl': 0, 'label': 'Net Profit', 'id': 'net_profit', 'values': {'2023': (net_profit, self._format_currency(net_profit))}, 'children': []}
        ]
        return {
            'years': ['2023'],
            'lines': lines
        }

    def _get_income_lines(self, domain, **kwargs):
        domain = domain + [('account_id.user_type_id.internal_group', '=', 'income')]
        overall_balance = self.read_group(domain, ['balance:sum'], ['company_id'])
        balance = abs(overall_balance and overall_balance[0].get('balance', 0) or 0)

        operating_income = self.read_group(domain + [('account_id.user_type_id', '=', self.env.ref('account.data_account_type_revenue').id)], ['balance:sum'], ['company_id'])
        operating_income_balance = abs(operating_income and operating_income[0].get('balance', 0) or 0)

        oi_accounts = self.read_group(domain + [('account_id.user_type_id', '=', self.env.ref('account.data_account_type_revenue').id)], ['balance:sum'], ['account_id'])

        operating_income_lines = []
        for oi_group in oi_accounts:
            oi_group_balance = abs(oi_group.get('balance', 0) or 0)
            operating_income_lines.append({
                'lvl': 3,
                'type': 'account',
                'label': oi_group.get('account_id')[1],
                'id': oi_group.get('account_id')[0],
                'values': {'2023': (oi_group_balance, self._format_currency(oi_group_balance))}
            })

        # account.data_account_type_direct_costs cost of revenue
        cost_of_revenue = self.read_group(domain + [('account_id.user_type_id', '=', self.env.ref('account.data_account_type_direct_costs').id)], ['balance:sum'], ['company_id'])
        cost_of_revenue_balance = 0
        cost_of_revenue_lines = []
        for cor_group in cost_of_revenue:
            cor_group_balance = abs(cor_group.get('balance', 0) or 0)
            cost_of_revenue_lines.append({
                'lvl': 3,
                'type': 'account',
                'label': cor_group.get('account_id')[1],
                'id': cor_group.get('account_id')[0],
                'values': {'2023': (cor_group_balance, self._format_currency(cor_group_balance))}
            })
            cost_of_revenue_balance += cor_group_balance

        children = [
            {'lvl': 1, 'type': 'summary', 'label': 'Gross Profit', 'id': 'gross_income', 'values': {'2023': (balance, self._format_currency(balance))}, 'children': []},
            {'lvl': 2, 'type': 'group', 'label': 'Operating Income', 'id': 'operating_income', 'values': {'2023': (operating_income_balance, self._format_currency(operating_income_balance))},
             'children': operating_income_lines},
        ]
        if cost_of_revenue_lines:
            children += [{'lvl': 2, 'type': 'group', 'label': 'Cost of Revenue', 'id': 'cost_of_revenue', 'values': {'2023': (cost_of_revenue_balance, self._format_currency(cost_of_revenue_balance))}, 
                          'children': cost_of_revenue_lines}]
        return balance, children
