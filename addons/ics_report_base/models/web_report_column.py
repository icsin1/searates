from odoo import models, fields, api


class WebReportColumn(models.Model):
    _name = 'web.report.column'
    _inherit = 'mixin.base.report.column'
    _description = 'Web Report Column'

    web_report_id = fields.Many2one('web.report', required=True, ondelete='cascade')
    expression_id = fields.Many2one('web.report.expression', compute='_compute_expression_id', store=True)

    @api.depends('expression_label', 'web_report_id.line_ids', 'web_report_id.line_ids.expression_ids', 'web_report_id.line_ids.expression_ids.name')
    def _compute_expression_id(self):
        for rec in self:
            expression = rec.web_report_id.line_ids.expression_ids.filtered(lambda expr: expr.name == rec.expression_label)
            rec.expression_id = expression and expression[0].id
