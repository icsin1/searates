# -*- coding: utf-8 -*-

from odoo import api, models, fields


class AccountAccount(models.Model):
    _inherit = 'account.account'

    create_asset = fields.Selection([('no', 'No'), ('draft', 'Create in draft'), ('validate', 'Create and Validate')],
                                    default='no', string="Automate Deferred")
    asset_model_id = fields.Many2one('account.asset', string="Asset")
    can_create_asset = fields.Boolean(string="Create Asset", compute="_compute_can_create_asset")
    asset_type = fields.Selection([("sale", "Deferred Revenue"), ("expense", "Deferred Expense"), ("asset", "Assets")], string="Deferred Type", compute="_compute_asset_type")

    @api.depends('user_type_id')
    def _compute_can_create_asset(self):
        """
        Deferred Asset can be possible if char of account type must in 'Fixed Asset', 'Non-current Asset' and 'Current Liabilities'.
        """
        allow_user_types = (self.env.ref('account.data_account_type_current_assets') |
                            self.env.ref('account.data_account_type_prepayments') |
                            self.env.ref('account.data_account_type_non_current_liabilities') |
                            self.env.ref('account.data_account_type_current_liabilities'))
        for account in self:
            account.can_create_asset = bool(account.user_type_id in allow_user_types)

    @api.depends('user_type_id')
    def _compute_asset_type(self):
        """ Set Asset type based on selection of User Type"""
        sale_types = self.env.ref('account.data_account_type_current_liabilities') | self.env.ref('account.data_account_type_non_current_liabilities')
        expense_types = self.env.ref('account.data_account_type_prepayments') | self.env.ref('account.data_account_type_current_assets')

        for account in self:
            if account.user_type_id in sale_types:
                account.asset_type = 'sale'
            elif account.user_type_id in expense_types:
                account.asset_type = 'expense'
            else:
                account.asset_type = ''
