from odoo import models
from odoo.osv import expression


class PartnerLedgerReportHandler(models.AbstractModel):
    _name = 'partner.ledger.report.handler'
    _inherit = 'mixin.report.handler'
    _description = 'Partner Ledger Report Handler'

    def _get_handler_domain(self, report, options, **kwargs):
        payable_domain = []
        receivable_domain = []
        non_trade_payable_domain = []
        non_trade_receivable_domain = []
        combined_domain = []
        filter_accounts = options.get('dynamic_filter_search', {}).get('filter_account', [])
        for filter_key in filter_accounts:
            if filter_key == 'payable':
                payable_domain = [('account_id.internal_type', '=', 'payable'), ('account_id.non_trade_payable', '=', False)]
            elif filter_key == 'non_trade_payable':
                non_trade_payable_domain = [('account_id.non_trade_payable', '=', True), ('account_id.internal_type', '=', 'payable')]
            elif filter_key == 'receivable':
                receivable_domain = [('account_id.internal_type', '=', 'receivable'), ('account_id.non_trade_payable', '=', False)]
            elif filter_key == 'non_trade_receivable':
                non_trade_receivable_domain = [('account_id.non_trade_payable', '=', True), ('account_id.internal_type', '=', 'receivable')]

            # Combine all domains using the OR operator
            combined_domain = expression.OR([
                payable_domain,
                non_trade_payable_domain,
                receivable_domain,
                non_trade_receivable_domain
            ])
        if not combined_domain:
            combined_domain = ['|', '|', ('account_id.internal_type', '=', 'payable'), ('account_id.internal_type', '=', 'receivable'), ('account_id.non_trade_payable', '=', False)]
        return super()._get_handler_domain(report, options, **kwargs) + combined_domain
