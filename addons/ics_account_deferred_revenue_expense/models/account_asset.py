# -*- coding: utf-8 -*-

import calendar
from lxml import etree
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, models, fields, _
from odoo.exceptions import UserError


def get_last_date_month(date):
    """
    Return last Date of the month which month's date passed in params.
    @param {date} date: current_date
    @return {date} last_date: last date of current month
    """
    nxt_mnth = date.replace(day=28) + timedelta(days=4)
    last_date = nxt_mnth - timedelta(days=nxt_mnth.day)
    return last_date


class AccountAsset(models.Model):
    _name = 'account.asset'
    _description = 'Account Asset'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def default_user_type_id(self):
        """To pass default context in chart of account based on asset type."""
        if self.env.context.get('default_asset_type') == 'sale':
            return self.env.ref('account.data_account_type_revenue').id
        if self.env.context.get('default_asset_type') == 'expense':
            return self.env.ref('account.data_account_type_current_assets').id

    def default_expense_user_type_id(self):
        """To pass default context in chart of account based on asset type."""
        if self.env.context.get('default_asset_type') == 'sale':
            return self.env.ref('account.data_account_type_current_liabilities').id
        if self.env.context.get('default_asset_type') == 'expense':
            return self.env.ref('account.data_account_type_expenses').id

    def _get_account_depreciation_domain(self):
        return "[('company_id', '=', company_id), ('deprecated', '=', False), ('internal_type', '=', 'other')]"

    def _get_account_depreciation_expense_domain(self):
        return "[('company_id', '=', company_id), ('deprecated', '=', False), ('internal_type', '=', 'other')]"

    def default_last_fy_date(self):
        """Return last date of the current financial year"""
        # _test_current_date is used for testing so do not remove otherwise test case will going to fail
        current_date = self.env.context.get("_test_current_date") or date.today()
        fiscal_date = self.env.company.compute_fiscalyear_dates(current_date)
        return fiscal_date.get('date_to') if fiscal_date else date.today() + relativedelta(months=1, day=1, days=-1)

    name = fields.Char(string="Name", required=True)
    recognition_interval = fields.Integer(string="Number of Recognitions", required=True, default=1, tracking=True, help="The number of depreciation needed to depreciate your asset.", copy=False)
    interval_period = fields.Selection([
        ('months', 'Months'),
        ('years', 'Years')
    ], string="Recognitions Interval Period", required=True, default='years', tracking=True, copy=False)
    company_id = fields.Many2one("res.company", string="Company", required=True, default=lambda self: self.env.company, readonly=True)
    currency_id = fields.Many2one('res.currency', required=True, readonly=True, default=lambda self: self.env.company.currency_id.id)
    journal_id = fields.Many2one("account.journal", string="Journal", required=True, domain="[('type', '=', 'general'), ('company_id', '=', company_id)]")
    state = fields.Selection([
        ('model', 'Model'),
        ("draft", "Draft"),
        ("running", "Running"),
        ("close", "Closed"),
        ("cancelled", "Cancelled")
    ], default="draft", string="Status", tracking=True, help="When an asset is created, the status is 'Draft'.\n "
                                                             "If the asset is confirmed, the status goes in 'Running' and the depreciation lines can be posted in the accounting."
                                                             "\n If the last line of depreciation is posted, the asset automatically goes in that status")
    active = fields.Boolean(default=True)
    asset_type = fields.Selection([
        ("sale", "Deferred Revenue"),
        ("expense", "Deferred Expense"),
        ("asset", "Assets")
    ], string="Deferred Type", required=True)
    prorata = fields.Boolean(string="Prorata", tracking=True,
                             help="If set, specifies the start date for the first period's computation. By default, it is set to the day's date rather the Start Date of the fiscal year.")
    prorata_date = fields.Date(string="Prorata Date", default=lambda self: fields.Date.context_today(self), tracking=True)
    first_recognition_date = fields.Date(string="First Recognition Date", default=default_last_fy_date)
    account_depreciation_id = fields.Many2one("account.account", string="Deferred Deprecation Account", required=True, domain=_get_account_depreciation_domain,
                                              help="Account used in the depreciation entries, to decrease the asset value.")
    account_depreciation_expense_id = fields.Many2one("account.account", string="Deferred Deprecation Expense Account", required=True, domain=_get_account_depreciation_expense_domain,
                                                      help="Account used in the periodical entries, to record a part of the asset as expense")
    original_value = fields.Monetary(string="Original Value", copy=False, tracking=True)
    acquisition_date = fields.Date(string="Acquisition Date", default=lambda self: fields.Date.context_today(self), tracking=True)
    residual_amount = fields.Monetary(string="Residual Amount to Recognize", readonly=True, copy=False)
    depreciation_move_ids = fields.One2many("account.move", "depreciation_id", string="Depreciation Lines")
    depreciated_entry_count = fields.Integer("Depreciation Entry Count", compute="_compute_depreciation_entry_count")
    total_depreciation_entry_count = fields.Integer("Depreciated Entry Count", compute="_compute_depreciation_entry_count")
    asset_move_id = fields.Many2one("account.move", string="Move")
    user_type_id = fields.Many2one('account.account.type', string="Account Type", default=default_user_type_id)
    expense_user_type_id = fields.Many2one('account.account.type', string="Account Type", default=default_expense_user_type_id)

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super(AccountAsset, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type in ['tree', 'form']:
            name = doc.xpath("//field[@name='name']")
            account_depreciation = doc.xpath("//field[@name='account_depreciation_id']")
            account_depreciation_expense = doc.xpath("//field[@name='account_depreciation_expense_id']")
            if self.env.context.get('default_asset_type') == 'sale':
                name[0].set("string", _("Revenue Name"))
                account_depreciation[0].set("string", _("Revenue Account"))
                account_depreciation_expense[0].set("string", _("Deferred Revenue Account"))
            if self.env.context.get('default_asset_type') == 'expense':
                name[0].set("string", _("Expenses"))
                account_depreciation[0].set("string", _("Deferred Expense Account"))
                account_depreciation_expense[0].set("string", _("Expense Account"))
            res['arch'] = etree.tostring(doc, encoding='unicode')
        if view_type == 'form':
            depreciation_lines = doc.xpath("//notebook/page[@name='depreciation_lines']")
            if self.env.context.get('default_asset_type') == 'sale':
                depreciation_lines[0].set("string", _("Revenue Board"))
            if self.env.context.get('default_asset_type') == 'expense':
                depreciation_lines[0].set("string", _("Expense Board"))
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    @api.onchange('original_value')
    def _onchange_residual_amount(self):
        for deferred in self:
            deferred.residual_amount = deferred.original_value if deferred.original_value else 0

    @api.onchange('prorata')
    def _onchange_prorata(self):
        for deferred in self:
            deferred.prorata_date = fields.Datetime.today() if deferred.prorata else False

    def _create_move_vals(self, ref, date, amount, remaining_amount, deprecated_amount):
        return {
            'move_type': _('entry'),
            'ref': ref,
            'date': date,
            'auto_post': True,
            'journal_id': self.journal_id.id,
            'amount_total': amount,
            'asset_remaining_value': remaining_amount,
            'asset_deprecated_value': deprecated_amount,
            'depreciation_id': self.id,
            'line_ids': [
                (0, 0, {'account_id': self.account_depreciation_id.id, 'credit': abs(amount), 'debit': 0}),
                (0, 0, {'account_id': self.account_depreciation_expense_id.id, 'debit': abs(amount), 'credit': 0}),
            ],
        }

    def button_compute_depreciation_board(self):
        """Create Journal Entries after confirming the assets."""
        self.ensure_one()

        if self.original_value == 0:
            return

        if self.depreciation_move_ids:
            self.depreciation_move_ids = [(6, False, [])]

        vals = []
        deprecated_amount = 0
        installment_amount = 0
        remaining_amount = self.original_value

        # _test_current_date is used for testing so do not remove otherwise test case will going to fail
        today_date = self.env.context.get("_test_current_date") or date.today()
        fiscal_date = self.env.company.compute_fiscalyear_dates(today_date)

        installment_amount += round(self.original_value / self.recognition_interval, 2)
        next_depreciation_date = self.first_recognition_date

        if self.prorata:
            if self.interval_period == 'months':
                last_date_mnth = get_last_date_month(self.prorata_date)
                total_days = abs(calendar.monthrange(last_date_mnth.year, last_date_mnth.month)[1])
                date_diff = self.prorata_date - get_last_date_month(self.prorata_date)
            else:
                total_days = abs(int((fiscal_date.get('date_to') - fiscal_date.get('date_from')).days)) + 1 if fiscal_date else 365
                date_diff = self.prorata_date - fiscal_date.get('date_to') if fiscal_date.get('date_to') else get_last_date_month(self.prorata_date)
            prorata_installment_amount = round((installment_amount / total_days) * (abs(int(date_diff.days)) + 1), 2)

            # Need to add because of last entry should not be zero
            if prorata_installment_amount >= installment_amount:
                self.prorata = self.prorata_date = False
            else:
                deprecated_amount += prorata_installment_amount
                remaining_amount -= prorata_installment_amount
                vals.append(self._create_move_vals(_('%s (prorata entry)' % self.name), next_depreciation_date, prorata_installment_amount, remaining_amount, deprecated_amount))

        for num in range(1, self.recognition_interval + 1):
            if round(remaining_amount) <= round(installment_amount):
                installment_amount = remaining_amount

            deprecated_amount += (installment_amount * num) if num == 1 and self.prorata else installment_amount
            remaining_amount -= installment_amount
            reference = self.name + ' ({}/{})'.format(num, self.recognition_interval)

            if self.interval_period == 'years':
                next_depreciation_date = next_depreciation_date if num == 1 and not self.prorata else next_depreciation_date + relativedelta(years=1)
            else:
                next_depreciation_date = next_depreciation_date if num == 1 and not self.prorata else get_last_date_month(next_depreciation_date + relativedelta(months=1))

            vals.append(self._create_move_vals(reference, next_depreciation_date, installment_amount, remaining_amount, round(deprecated_amount, 2)))

        return self.env['account.move'].create(vals)

    def button_confirm(self):
        for rec in self:
            rec.state = 'running'

            # Create Journal Entry
            rec.button_compute_depreciation_board()

            for move in rec.depreciation_move_ids.filtered(lambda line: line.state == 'draft'):
                # _test_current_date is used for testing so do not remove otherwise test case will going to fail
                today_date = rec.env.context.get("_test_current_date", date.today())
                if move.date <= today_date:
                    move.auto_post = False
                    move.action_post()

    def button_set_to_draft(self):
        self.state = 'draft'

    def action_open_journal_entries(self):
        """Open records for the Journal Entries (Smart button)"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Journal Entries'),
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', self.depreciation_move_ids.ids)],
            'context': "{'create': False}"
        }

    @api.depends('depreciation_move_ids', 'depreciation_move_ids.state')
    def _compute_depreciation_entry_count(self):
        for asset in self:
            asset.depreciated_entry_count = len(asset.depreciation_move_ids.filtered(lambda move: move.state != 'draft').ids) if asset.depreciation_move_ids else 0
            asset.total_depreciation_entry_count = len(asset.depreciation_move_ids.ids) if asset.depreciation_move_ids else 0

    def unlink(self):
        for asset in self:
            if asset.state in ['running', 'paused', 'close'] and not self.env.user.has_group('account.group_account_manager'):
                raise UserError(_("You cannot delete a record that is in {} state.").format(asset.state.capitalize()))
        return super().unlink()

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        chosen_name = default.get('name') if default else ''
        new_name = chosen_name or _('%s (copy)', self.name)
        default = dict(default or {}, name=new_name)
        return super(AccountAsset, self).copy(default)

    @api.onchange('interval_period')
    def _onchange_interval_period(self):
        for deferred in self:
            # _test_current_date is used for testing so do not remove otherwise test case will going to fail
            current_date = self.env.context.get("_test_current_date") or date.today()
            deferred.first_recognition_date = self.default_last_fy_date() if deferred.interval_period == 'years' else get_last_date_month(current_date)
