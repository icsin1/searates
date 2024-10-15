# -*- coding: utf-8 -*-

from odoo import models, fields, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    tds_receivable_account_id = fields.Many2one('account.account', string="TDS Receivable Account",
                                                related='company_id.tds_receivable_account_id', readonly=False)
    tds_payable_account_id = fields.Many2one('account.account', string="TDS Payable Account",
                                             related='company_id.tds_payable_account_id', readonly=False)
    calculate_tds = fields.Boolean(related="company_id.calculate_tds", string="Calculate TDS", readonly=False)
