from odoo import models, _


class AccountGeneralTrialBalanceHandler(models.AbstractModel):
    _name = 'account.general.trial.balance.handler'
    _inherit = 'account.general.ledger.handler'
    _description = 'Account Trial Balance Handler'

    def _get_report_filename(self, report, options, **kwargs):
        return _('Trial Balance')

    def _get_report_title(self, report):
        return _('Trial Balance')
