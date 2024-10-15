# -*- coding: utf-8 -*-

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    pdc_receivable_account_id = fields.Many2one('account.account', string='PDC Receivable Account')
    pdc_payable_account_id = fields.Many2one('account.account', string='PDC Payable Account')
