# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pdc_receivable_account_id = fields.Many2one(
        'account.account',
        string='PDC Receivable Account',
        readonly=False,
        related='company_id.pdc_receivable_account_id')
    pdc_payable_account_id = fields.Many2one(
        'account.account',
        string='PDC Payable Account',
        readonly=False,
        related='company_id.pdc_payable_account_id')
