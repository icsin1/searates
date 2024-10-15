# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    allow_reference_number = fields.Boolean('Custom Reference Number')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_reference_number = fields.Boolean('Custom Reference Number', related='company_id.allow_reference_number', readonly=False)
    enable_adjust_payment_multi_currency = fields.Boolean(related='company_id.enable_adjust_payment_multi_currency', readonly=False)
    # Module to manage Deferred Revenue/Expense in accounting
    module_ics_account_deferred_revenue_expense = fields.Boolean(default=False)
    module_ics_account_pdc = fields.Boolean(default=False, string='PDC Payments')
    module_ics_account_lumpsum_discount = fields.Boolean(default=False, string='Discount')
    fiscalyear_last_month = fields.Selection(related='company_id.fiscalyear_last_month', required=True, readonly=False)
    fiscalyear_last_day = fields.Integer(related='company_id.fiscalyear_last_day', required=True, readonly=False)
