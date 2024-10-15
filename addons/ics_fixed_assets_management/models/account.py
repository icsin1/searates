# -*- coding: utf-8 -*-

from lxml import etree
from odoo import api, models, fields, _


class AccountAccount(models.Model):
    _inherit = 'account.account'

    manage_asset_per_line = fields.Boolean(string="Manage Items",
                                           help="Multiple asset items will be generated depending on the bill line quantity instead of 1 global asset.")

    @api.depends('user_type_id')
    def _compute_can_create_asset(self):
        """
        Inherited for the Fixed Asset management.
        Asset is allowed in fixed asset and non-current asset.
        """
        allow_user_types = (self.env.ref('account.data_account_type_fixed_assets') |
                            self.env.ref('account.data_account_type_non_current_assets'))
        can_create_asset_ids = self.filtered(lambda acc: acc.user_type_id in allow_user_types)
        can_create_asset_ids.write({'can_create_asset': True})
        return super(AccountAccount, self - can_create_asset_ids)._compute_can_create_asset()

    @api.depends('user_type_id')
    def _compute_asset_type(self):
        """ Inherited for the Fixed Asset management. """
        asset_types = self.env.ref('account.data_account_type_fixed_assets') | self.env.ref('account.data_account_type_non_current_assets')

        asset_type_accounts = self.filtered(lambda acc: acc.user_type_id in asset_types)
        asset_type_accounts.write({'asset_type': 'asset'})
        return super(AccountAccount, self - asset_type_accounts)._compute_asset_type()

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super(AccountAccount, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        account_id = self.browse(self.env.context.get('active_id'))
        if view_type == 'form' and account_id.asset_type == 'asset':
            asset_model_id = doc.xpath("//field[@name='asset_model_id']")
            asset_model_id[0].set("string", _("Asset Model"))
        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res
