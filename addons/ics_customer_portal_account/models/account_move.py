# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    def calculate_days(self):
        days = ''
        if self.invoice_date:
            return (fields.Date.today() - self.invoice_date).days
        return days
