from odoo import models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def button_undo_reconciliation(self):
        super().button_undo_reconciliation()
        for record in self:
            record.statement_id.move_line_ids.statement_line_id = False
