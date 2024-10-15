# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    depreciation_id = fields.Many2one("account.asset", string="Depreciation", ondelete='cascade')
    asset_deprecated_value = fields.Monetary(string="Cumulative Expense", readonly=True)
    asset_remaining_value = fields.Monetary(string="Next Period Expense", readonly=True)
    account_asset_ids = fields.One2many("account.asset", "asset_move_id", string="Assets")
    display_name_deferred_asset = fields.Char("Deferred Assets Count", compute="_compute_display_name_deferred_asset")

    def action_open_deferred_assets(self):
        """Smart button for the Account Assets (Deferred Revenue/Expense)"""
        self.ensure_one()

        name = ""
        asset_type = False
        move_type_mapping = {
            "out_invoice": _("Deferred Revenue(s)"),
            "out_refund": _("Deferred Revenue(s)"),
            "in_invoice": _("Deferred Expense(s)"),
            "in_refund": _("Deferred Expense(s)"),
        }

        if self.move_type in move_type_mapping:
            name = move_type_mapping[self.move_type]
            asset_type = 'sale' if self.move_type in ["out_invoice", "out_refund"] else 'expense'

        return {
            'type': "ir.actions.act_window",
            'name': name,
            'view_mode': "tree,form",
            'res_model': "account.asset",
            'domain': [("id", "in", self.account_asset_ids.ids)],
            'context': {'create': False, 'default_asset_type': asset_type}
        }

    def _compute_display_name_deferred_asset(self):
        """Visible string on smart button for Account Assets (Deferred Revenue/Expense)"""
        for asset in self:
            display_name_deferred_asset = ""
            asset_count = len(asset.account_asset_ids.ids) if asset.account_asset_ids else 0
            move_type_mapping = {
                "out_invoice": _("%s Deferred Revenue(s)") % str(asset_count),
                "out_refund": _("%s Deferred Revenue(s)") % str(asset_count),
                "in_invoice": _("%s Deferred Expense(s)") % str(asset_count),
                "in_refund": _("%s Deferred Expense(s)") % str(asset_count),
            }
            if asset.move_type in move_type_mapping:
                display_name_deferred_asset = move_type_mapping[asset.move_type]
            asset.display_name_deferred_asset = display_name_deferred_asset

    def action_post(self):
        """inherit of the function from account.move to validate deferred revenue/expense."""
        res = super().action_post()
        for move_line in self.invoice_line_ids.filtered(lambda line: line.move_id.move_type != 'entry' and line.account_id and line.account_id.create_asset != 'no'):
            asset_ids = self.with_context(self.env.context).create_account_assets(move_line)
            asset_ids.write({'asset_move_id': self.id})
        for move in self:
            if not move.depreciation_id.depreciation_move_ids.filtered(lambda line: line.state == 'draft'):
                move.depreciation_id.state = 'close'
            deprecated_amount = move.depreciation_id.residual_amount
            move.depreciation_id.residual_amount = deprecated_amount - move.amount_total
        return res

    def create_account_assets(self, line_id):
        """Create Deferred Revenue/Expenses."""
        original_value = line_id.currency_id._convert(line_id.price_subtotal, self.env.company.currency_id, self.company_id, line_id.move_id.date)
        ref_name = line_id.name
        if not ref_name:
            raise ValidationError(_("Please add product's Label to create deferred Revenue/Expense."))
        vals = {
            'name': ref_name,
            'original_value': original_value,
            'account_depreciation_id': line_id.account_id.asset_model_id.account_depreciation_id.id if line_id.account_id.asset_model_id else False,
            'account_depreciation_expense_id': line_id.account_id.asset_model_id.account_depreciation_expense_id.id if line_id.account_id.asset_model_id else False,
            'journal_id': line_id.account_id.asset_model_id.journal_id.id if line_id.account_id.asset_model_id else line_id.journal_id.id,
            'recognition_interval': line_id.account_id.asset_model_id.recognition_interval if line_id.account_id.asset_model_id else 1,
            'interval_period': line_id.account_id.asset_model_id.interval_period if line_id.account_id.asset_model_id else 'years',
            'asset_type': line_id.account_id.asset_model_id.asset_type if line_id.account_id.asset_model_id else False,
            'prorata': line_id.account_id.asset_model_id.prorata if line_id.account_id.asset_model_id else False,
            'acquisition_date': line_id.move_id.invoice_date,
        }
        asset_id = self.env['account.asset'].create(vals)

        asset_id._onchange_interval_period()
        asset_id._onchange_residual_amount()

        # Validate deferred revenue/expenses
        if line_id.account_id.create_asset == 'validate':
            asset_id.button_confirm()
        return asset_id
