from odoo import api, models
from odoo.osv import expression


class AccountReconciliation(models.AbstractModel):
    _inherit = "account.reconciliation.widget"

    @api.model
    def _domain_move_lines_for_reconciliation(self, st_line, aml_accounts, partner_id, excluded_ids=None,
                                              search_str=False, mode="rp"):
        domain = super()._domain_move_lines_for_reconciliation(st_line, aml_accounts, partner_id,
                                                               excluded_ids=excluded_ids, search_str=search_str,
                                                               mode=mode)
        journal_id = self._context.get('journal_id')
        domain = expression.AND([domain, ['|', ('journal_id', '=', journal_id), ('journal_id.type', '!=', 'bank')]])
        if mode == "rp":
            domain = expression.AND(
                [
                    domain,
                    [
                        (
                            "account_id.internal_type",
                            "in",
                            ["receivable", "payable", "liquidity", "other"],
                        ),
                        ('amount_residual', '!=', 0),
                        ('reconciled', '!=', True),
                    ],
                ]
            )
        else:
            domain = expression.AND(
                [
                    domain,
                    [(
                        "account_id.internal_type",
                        "not in",
                        ["receivable", "payable",],
                    ),
                        ('amount_residual', '!=', 0),
                        ('move_id.payment_id', '=', False),
                        ('reconciled', '!=', True),
                    ],
                ]
            )
        return domain
