# -*- coding: utf-8 -*-

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    enable_adjust_payment_multi_currency = fields.Boolean(default=True)
