# -*- coding: utf-8 -*-

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    # def get_tds_receivable_account(self):
    #     return self.env.ref('l10n_in.1_p10054')

    # def get_tds_payable_account(self):
    #     return self.env.ref('l10n_in.1_p11231')

    # NOTE: Removed default as direct ref can not work if india company ID is second.
    tds_receivable_account_id = fields.Many2one('account.account', string="TDS Receivable Account")
    tds_payable_account_id = fields.Many2one('account.account', string="TDS Payable Account")
    calculate_tds = fields.Boolean(string="Calculate TDS")
