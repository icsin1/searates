from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_shipping_line_free_time = fields.Boolean(string='Enable Free Time', related='company_id.enable_shipping_line_free_time', readonly=False)
