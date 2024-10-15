from odoo import models, fields, api
from odoo import tools


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    theme_menu_icon = fields.Image()
    theme_menu_access_allowed = fields.Boolean(default=False, help="If True, theme will allow to load this menu to user")

    def read(self, fields=None, load='_classic_read'):
        fields = (fields or []) + ['theme_menu_icon']
        return super().read(fields, load)

    @api.model
    @api.returns('self')
    def get_user_roots(self):
        menus = super().get_user_roots()
        if not self.env.user.user_has_groups('odoo_base.group_odoo_all_menu_access'):
            menus = menus.filtered(lambda m: m.theme_menu_access_allowed)
        return menus

    @api.model
    @tools.ormcache_context('self._uid', 'debug', keys=('lang',))
    def load_menus(self, debug):
        return super(IrUiMenu, self.with_context(additional_fields=[
            'theme_menu_icon'
        ])).load_menus(debug=debug)
