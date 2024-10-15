from odoo import models, _


class AccountFinanceCashFlowReport(models.Model):
    _name = 'account.finance.cash.flow.report'
    _inherit = 'account.finance.report.mixin'
    _description = 'Account Finance Cash Flow Report'

    def get_account_report_data(self, domain, **kwargs):
        return {
            'title': _('Cash Flow Statement'),
            'attrs': {
                'control_panel': False
            },
            'sections': self._get_sections(domain, **kwargs),
            'columns': [_('Balance')]
        }

    def _get_sections(self, domain, **kwargs):
        return [
            self._get_opening_balance(domain, **kwargs),
            self._get_increase_in_cash_by_operations(domain, **kwargs),
            self._get_closing_balance(domain, **kwargs)
        ]

    def _get_opening_balance(self, domain, **kwargs):
        return {
            'id': 'cash_opening',
            'title': _('Cash and cash equivalents, beginning of period'),
            'code': 'OPEN',
            'level': 0,
            'group_by': 'account_id',
            'children': [],
            'values': {'Balance': (0, 0)}
        }

    def _get_increase_in_cash_by_operations(self, domain, **kwargs):
        return {
            'id': 'cash_operations',
            'title': _('Net increase in cash and cash equivalents'),
            'code': 'OPE',
            'level': 0,
            'group_by': False,
            'children': [],
            'values': {'Balance': (0, 0)}
        }

    def _get_closing_balance(self, domain, **kwargs):
        domain += [('account_id.user_type_id', '=', self.env.ref('account.data_account_type_liquidity').id)]
        # groups = self._get_account_values(domain, ['balance:sum'], ['company_id'])
        return {
            'id': 'cash_closing',
            'title': _('Cash and cash equivalents, closing balance'),
            'code': 'CLOSE',
            'level': 0,
            'group_by': 'account_id',
            'children': [],
            'values': {'Balance': (0, 0)}
        }
