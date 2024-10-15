# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_fm_transportation_container_option = fields.Boolean(default=False, string='Enable Container & Transportation Details', help="Add Container & Transportation Details at quote and "
                                                                                                                                       "opportunity level")

    @api.onchange('module_fm_transportation_container_option')
    def _onchange_module_fm_transportation_container_option(self):
        res = {}
        if self.module_fm_transportation_container_option:
            if self.env['ir.module.module'].search([('name', '=', 'fm_transportation_container_option'), ('state', '=', 'uninstalled')]):
                res['warning'] = {
                    'title': _('Warning!'),
                    'message': _('From Opportunity and Quotation, your Packages/Container and Transportation Details will be lost.')
                }
        return res
