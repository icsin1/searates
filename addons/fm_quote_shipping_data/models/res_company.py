from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    enable_shipping_line_free_time = fields.Boolean(string='Enable Free Time', readonly=False)
