from odoo import models, fields


class WebReport(models.Model):
    _inherit = 'web.report'

    is_account_report = fields.Boolean(default=False)
    is_tax_report = fields.Boolean(default=False)
    country_id = fields.Many2one('res.country')
