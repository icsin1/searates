# -*- coding:utf-8 -*-

from odoo import fields, models, api


class ReportOutputType(models.Model):
    _name = "report.output.type"
    _description = 'Report Output Type'
    _order = 'sequence'

    name = fields.Char(string='Report Output Type')
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=0)


class ReportType(models.Model):
    _name = "report.type"
    _description = 'Report Type'

    report_type_id = fields.Many2one('report.output.type', string="Report Type")
    has_repeat_count = fields.Integer(string='Repeat Doc', compute='_compute_has_repeat_count', readonly=False)
    show_count = fields.Boolean(compute='_compute_show_count')

    @api.depends('report_type_id')
    def _compute_has_repeat_count(self):
        for report in self:
            if report.has_repeat_count:
                report.has_repeat_count = report.has_repeat_count
            else:
                record_id = self.env.context.get('res_id')
                model = self.env.context.get('res_model')
                if record_id and model and report.report_type_id:
                    record = self.env[model].browse(record_id)
                    report.has_repeat_count = getattr(record, self.get_field_name(), 0)
                    continue

                report.has_repeat_count = 0

    @api.depends('report_type_id')
    def _compute_show_count(self):
        for report in self:
            if report.report_type_id.id == self.env.ref('base_document_reports.report_output_type_original').id:
                report.show_count = True
            elif report.report_type_id.id == self.env.ref('base_document_reports.report_output_type_copies').id:
                report.show_count = True
            else:
                report.show_count = False

    def get_field_name(self):
        self.ensure_one()

        if self.report_type_id.id == self.env.ref('base_document_reports.report_output_type_original').id:
            return 'no_of_origin_docs'
        elif self.report_type_id.id == self.env.ref('base_document_reports.report_output_type_copies').id:
            return 'no_of_copy_docs'
        return ''
