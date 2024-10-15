# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def fields_view_get(self, view_id=None, view_type='tree', toolbar=False,submenu=False):
        res = super(ProductTemplate, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        is_charge_check = self.env['ir.config_parameter'].sudo().get_param('freight_management.charge_migration')
        charge_migration_id = self.env.ref('freight_management_charges.action_charge_master_migration').id
        if not is_charge_check:
            for button in res.get('toolbar', {}).get('action', []):
                if button['id'] == charge_migration_id:
                    res['toolbar']['action'].remove(button)
        return res


    def action_charge_master_popup(self):
        return {
            'name': 'Import Charges',
            'res_model': 'import.charges',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'product_ids': self.ids}
        }
