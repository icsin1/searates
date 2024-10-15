# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    view_customization = fields.Selection([
        ('all', 'All Users are allowed to modify screen'),
        ('admin', ' Admin level they modify and available for all'),
        ('admin_only', ' Admin level they modify Only for Admin'),
    ], 'View Customize', default='all', required=True)

    def write(self, values):
        if 'view_customization' in values:
            # Cleanup old customized views
            self.env['ir.ui.view'].sudo().search([('is_custom', '=', True)]).unlink()
        return super().write(values)
