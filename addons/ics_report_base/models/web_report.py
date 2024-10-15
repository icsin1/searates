from odoo import models, fields


class WebReport(models.Model):
    _name = 'web.report'
    _inherit = 'mixin.base.report'
    _description = 'Web Report'

    column_ids = fields.One2many('web.report.column', 'web_report_id', string='Columns')
    line_ids = fields.One2many('web.report.line', 'web_report_id', string='Lines/Sections')
    filter_ids = fields.One2many('web.report.filter', 'web_report_id', string='Filters')
