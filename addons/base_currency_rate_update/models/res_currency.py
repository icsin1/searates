# -*- coding: utf-8 -*-

from odoo import models, api


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        res = super().search(args, offset, limit, order, count)
        if len(args) == 1:
            if 'id' in args[0]:
                return res
        if self._context and self._context.get('show_company_currency_first') and res and isinstance(res, models.Model):
            return self.modified_currency_list(res)
        return res

    def modified_currency_list(self, currencies):
        """
        Modify the list of currencies to show the company currency first.
        """
        company_currency = self.env.company.currency_id
        return company_currency + (currencies - company_currency)
