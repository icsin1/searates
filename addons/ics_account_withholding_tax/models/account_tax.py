# -*- coding: utf-8 -*-
from odoo import models, fields


class AccountTax(models.Model):
    _inherit = 'account.tax'

    tax_on_payment = fields.Boolean('Tax on Payment', tracking=True, copy=False)
