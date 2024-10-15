from odoo import models, fields, api, modules
from odoo.addons.base.models.ir_module import assert_log_admin_access


class IrModuleModule(models.Model):
    _inherit = "ir.module.module"

    active = fields.Boolean(default=True)

    @assert_log_admin_access
    @api.model
    def update_list(self):
        ir_module_module_obj = self.env['ir.module.module'].sudo()
        for mod_name in modules.get_modules():
            ir_module_module_id = ir_module_module_obj.search([('name', '=', mod_name), ('active', '=', False), ('to_buy', '=', False)])
            if ir_module_module_id:
                ir_module_module_id.write({'active': True})
        return super().update_list()
