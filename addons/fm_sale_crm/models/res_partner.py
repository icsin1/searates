from odoo import models, fields, api
from odoo.osv import expression


class ResPartner(models.Model):
    _inherit = "res.partner"

    govt_reg_number = fields.Char(string="Govt. Registration No.")

    @api.model
    def _where_calc(self, domain, active_test=True):
        if self._context and self._context.get('organization'):
            if self.env.user.has_group('fm_sale_crm.group_salesman') and not self.env.user.has_group('fm_sale_crm.group_sales_manager') and \
                    not self.env.user.has_group('fm_sale_crm.group_sales_administrator'):
                domain = expression.AND(
                    [
                        domain,
                        ['|', ('user_id', '=', self.env.user.id), ('create_uid', '=', self.env.user.id)],
                    ]
                )
        return super()._where_calc(domain, active_test=active_test)
