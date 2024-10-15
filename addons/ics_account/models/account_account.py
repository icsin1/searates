from odoo import models, fields


class AccountAccount(models.Model):
    _inherit = 'account.account'

    user_type_internal_group = fields.Selection(related='user_type_id.internal_group', store=True, string='Parent Type')
    non_trade_payable = fields.Boolean(string='Non Trade', default=False)
    active = fields.Boolean(default=True, string='Archive')
