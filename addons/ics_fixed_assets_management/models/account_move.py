# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _compute_display_name_deferred_asset(self):
        """Visible string on smart button for Account Assets (Deferred Revenue/Expense)"""
        move_ids = self.filtered(lambda asset: asset.account_asset_ids and 'asset' in asset.account_asset_ids.mapped('asset_type'))
        for move in move_ids:
            move.write({'display_name_deferred_asset': _("%s Asset(s)") % str(len(move.account_asset_ids.ids))})
        return super(AccountMove, self - move_ids)._compute_display_name_deferred_asset()

    def action_open_deferred_assets(self):
        """Smart button for the Account Assets (Deferred Revenue/Expense)"""
        self.ensure_one()
        if 'asset' in self.account_asset_ids.mapped('asset_type'):
            return {
                'type': "ir.actions.act_window",
                'name': _("Asset"),
                'view_mode': "tree,form",
                'views': [[self.env.ref('ics_fixed_assets_management.fixed_asset_view_tree').id, 'tree'],
                          [self.env.ref('ics_fixed_assets_management.account_asset_view_form_inherited_fixed_asset').id, 'form']],
                'res_model': "account.asset",
                'domain': [("id", "in", self.account_asset_ids.ids)],
                'context': {'create': False, 'default_asset_type': 'asset'}
            }
        else:
            return super().action_open_deferred_assets()

    def get_asset_vals(self, line_id, original_value):
        return {
            'name': line_id.name,
            'original_value': original_value,
            'account_depreciation_id': line_id.account_id.asset_model_id.account_depreciation_id.id,
            'account_depreciation_expense_id': line_id.account_id.asset_model_id.account_depreciation_expense_id.id,
            'journal_id': line_id.account_id.asset_model_id.journal_id.id,
            'recognition_interval': line_id.account_id.asset_model_id.recognition_interval,
            'interval_period': line_id.account_id.asset_model_id.interval_period,
            'asset_type': line_id.account_id.asset_model_id.asset_type,
            'prorata': line_id.account_id.asset_model_id.prorata,
            'acquisition_date': line_id.move_id.invoice_date,
            'account_asset_id': line_id.account_id.asset_model_id.account_asset_id.id if line_id.account_id.asset_model_id.account_asset_id else False,
            'method': line_id.account_id.asset_model_id.method,
            'declining_factor': line_id.account_id.asset_model_id.declining_factor,
        }

    def create_account_assets(self, line_id):
        if line_id.account_id.asset_model_id.asset_type == 'asset' and line_id.move_id.move_type not in ['in_invoice', 'in_refund']:
            return self.env['account.asset']
        elif line_id.account_id.asset_model_id and line_id.account_id.asset_model_id.asset_type == 'asset':
            asset_ids_list = []
            vals = []
            if not line_id.name:
                raise ValidationError(_("Please add product's Label."))
            if line_id.account_id.manage_asset_per_line:
                original_value = line_id.currency_id._convert(line_id.price_subtotal / line_id.quantity, self.env.company.currency_id, self.company_id, line_id.move_id.date)
                for line in range(0, int(line_id.quantity)):
                    asset_vals = self.get_asset_vals(line_id, original_value)
                    vals.append(asset_vals)
            else:
                original_value = line_id.currency_id._convert(line_id.price_subtotal, self.env.company.currency_id, self.company_id, line_id.move_id.date)
                asset_vals = self.get_asset_vals(line_id, original_value)
                vals.append(asset_vals)
            asset_ids = self.env['account.asset'].create(vals)

            asset_ids._onchange_interval_period()
            asset_ids._onchange_residual_amount()

            # Validate deferred revenue/expenses
            if line_id.account_id.create_asset == 'validate':
                asset_ids.button_confirm()
            asset_ids_list.append(asset_ids)
            return asset_ids
        else:
            return super().create_account_assets(line_id)
