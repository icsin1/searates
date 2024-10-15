# -*- coding: utf-8 -*-

import calendar
from datetime import date
from lxml import etree
from odoo import api, models, fields, _
from dateutil.relativedelta import relativedelta
from odoo.addons.ics_account_deferred_revenue_expense.models.account_asset import get_last_date_month


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    def _get_account_asset_domain(self):
        allow_user_type = self.env.ref('account.data_account_type_fixed_assets')
        return "[('company_id', '=', company_id), ('deprecated', '=', False), ('internal_type', '=', 'other'), ('user_type_id', 'in', %s)]" % allow_user_type.ids

    def _get_account_depreciation_domain(self):
        domain = [('company_id', '=', self.env.company.id), ('deprecated', '=', False), ('internal_type', '=', 'other')]
        if self.env.context.get('default_asset_type') == 'asset':
            allow_user_type = self.env.ref('account.data_account_type_fixed_assets')
            domain += [('user_type_id', 'in', allow_user_type.ids)]
            return domain
        else:
            return super()._get_account_depreciation_domain()

    def _get_account_depreciation_expense_domain(self):
        domain = [('company_id', '=', self.env.company.id), ('deprecated', '=', False), ('internal_type', '=', 'other')]
        if self.env.context.get('default_asset_type') == 'asset':
            allow_user_type = self.env.ref('account.data_account_type_depreciation')
            domain += [('user_type_id', 'in', allow_user_type.ids)]
            return domain
        else:
            return super()._get_account_depreciation_expense_domain()

    account_asset_id = fields.Many2one("account.account", string="Fixed Asset Account", domain=_get_account_asset_domain,
                                       help="Account used to record the purchase of the asset at its original.")
    method = fields.Selection([
        ('line', 'Straight Line'),
        ('decline', 'Declining')
    ], default="line",
        help="Choose the method to use to compute the amount of depreciation lines."
             "\n * Straight Line: Calculated on basis of: Gross Value / Number of Depreciations"
             "\n * Declining: Calculated on basis of: Residual Value * Declining Factor % ")
    declining_factor = fields.Float(string="Declining Factor")
    book_value = fields.Monetary(string='Book Value', compute="_compute_book_value", readonly=True, recursive=True, store=True)
    non_depreciable_value = fields.Monetary(string='Not Depreciable Value')
    account_depreciation_id = fields.Many2one("account.account", string="Deferred Deprecation Account", required=True, domain=_get_account_depreciation_domain,
                                              help="Account used in the depreciation entries, to decrease the asset value.")
    account_depreciation_expense_id = fields.Many2one("account.account", string="Deferred Deprecation Expense Account", required=True, domain=_get_account_depreciation_expense_domain,
                                                      help="Account used in the periodical entries, to record a part of the asset as expense")

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super(AccountAsset, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type in ['tree', 'form']:
            account_depreciation = doc.xpath("//field[@name='account_depreciation_id']")
            account_depreciation_expense = doc.xpath("//field[@name='account_depreciation_expense_id']")
            residual_amount = doc.xpath("//field[@name='residual_amount']")
            if self.env.context.get('default_asset_type') == 'asset':
                account_depreciation[0].set("string", _("Depreciation Account"))
                account_depreciation_expense[0].set("string", _("Expense Account"))
                if self.env.context.get('default_state') != 'model':
                    residual_amount[0].set("string", _("Depreciable Value"))
        if view_type == 'form':
            if self.env.context.get('default_asset_type') == 'asset' and self.env.context.get('default_state') != 'model':
                depreciation_lines = doc.xpath("//notebook/page[@name='depreciation_lines']")
                depreciation_lines[0].set("string", _("Depreciation Board"))
        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    @api.depends('residual_amount', 'non_depreciable_value', 'book_value')
    def _compute_book_value(self):
        for record in self:
            depreciated_value = sum(record.depreciation_move_ids.filtered(lambda move: move.state == 'posted').mapped('amount_total'))
            record.book_value = record.original_value - depreciated_value

    @api.onchange('original_value', 'non_depreciable_value')
    def _onchange_residual_amount(self):
        res = super()._onchange_residual_amount()
        for deferred in self:
            if deferred.asset_type != 'asset':
                return res
            else:
                deferred.residual_amount = deferred.original_value - deferred.non_depreciable_value

    def get_depreciation_amount(self, depreciable_value):
        """
        :param depreciable_value: Amount calculation based on total amount of invoice/vendor bill by method
        :return depreciation_amount: 1st depreciate amount (Based on calculation)
        """
        depreciation_amount = 0
        if self.method == 'decline':
            depreciation_amount += depreciable_value * (self.declining_factor / 100)
        else:
            depreciation_amount += self.residual_amount / self.recognition_interval
        return round(depreciation_amount, 2)

    def get_prorata_amount(self, depreciable_value, deprecated_amount):
        """
        :param depreciable_value: Amount calculation based on total amount of invoice/vendor bill by method
        :param deprecated_amount: 1st depreciate amount (Based on calculation) (default it will be 0)
        :return depreciable_value: Total amount - first depreciation amount
        :return deprecated_amount: 1st depreciate amount (Based on calculation)
        :return prorata_depreciation_amount: 1st depreciate amount (Based on calculation)
        """
        # _test_current_date is used for testing so do not remove otherwise test case will going to fail
        today_date = self.env.context.get("_test_current_date") or date.today()
        fiscal_date = self.env.company.compute_fiscalyear_dates(today_date)
        depreciation_amount = self.get_depreciation_amount(depreciable_value)
        vals = {}
        if self.interval_period == 'months':
            last_date_mnth = get_last_date_month(self.prorata_date)
            total_days = abs(calendar.monthrange(last_date_mnth.year, last_date_mnth.month)[1])
            date_diff = self.prorata_date - get_last_date_month(self.prorata_date)
        else:
            total_days = abs(int((fiscal_date.get('date_to') - fiscal_date.get('date_from')).days)) + 1 if fiscal_date else 365
            date_diff = self.prorata_date - fiscal_date.get('date_to') if fiscal_date.get('date_to') else get_last_date_month(self.prorata_date)
        prorata_depreciation_amount = round((depreciation_amount / total_days) * (abs(int(date_diff.days)) + 1), 2)

        # Need to add because of last entry should not be zero
        if prorata_depreciation_amount >= depreciation_amount:
            self.prorata = self.prorata_date = False
            vals.update({
                'prorata': False
            })
        else:
            deprecated_amount += prorata_depreciation_amount
            depreciable_value -= prorata_depreciation_amount
            vals.update({
                'depreciable_value': round(depreciable_value, 2),
                'deprecated_amount': round(deprecated_amount, 2),
                'prorata_depreciation_amount': round(prorata_depreciation_amount, 2),
            })
        return vals

    def button_compute_depreciation_board(self):
        """ Inherit for the change calculation of asset depreciations """
        asset_ids = self.filtered(lambda acc: acc.asset_type == 'asset' and acc.original_value != 0)
        if not asset_ids:
            return super().button_compute_depreciation_board()
        vals = []
        for rec in asset_ids:
            if rec.depreciation_move_ids:
                rec.depreciation_move_ids = [(6, False, [])]

            depreciable_value = rec.residual_amount
            deprecated_amount = 0
            next_depreciation_date = rec.first_recognition_date

            if rec.prorata:
                prorata_vals = rec.get_prorata_amount(depreciable_value, deprecated_amount)
                if 'prorata' not in prorata_vals:
                    depreciable_value = prorata_vals.get('depreciable_value')
                    deprecated_amount = prorata_vals.get('deprecated_amount')
                    vals.append(rec._create_move_vals(_('%s (prorata entry)' % rec.name), next_depreciation_date, prorata_vals.get('prorata_depreciation_amount'),
                                                      depreciable_value, prorata_vals.get('deprecated_amount')))

            for num in range(1, rec.recognition_interval + 1):
                reference = rec.name + ' ({}/{})'.format(num, rec.recognition_interval)
                depreciation_amount = rec.get_depreciation_amount(depreciable_value)
                if num == rec.recognition_interval:
                    depreciation_amount = depreciable_value
                depreciable_value -= depreciation_amount
                deprecated_amount += depreciation_amount
                if rec.interval_period == 'years':
                    next_depreciation_date = next_depreciation_date if num == 1 and not rec.prorata else next_depreciation_date + relativedelta(years=1)
                else:
                    next_depreciation_date = next_depreciation_date if num == 1 and not rec.prorata else get_last_date_month(next_depreciation_date + relativedelta(months=1))
                vals.append(rec._create_move_vals(reference, next_depreciation_date, depreciation_amount, depreciable_value, round(deprecated_amount, 2)))
        return self.env['account.move'].create(vals)
