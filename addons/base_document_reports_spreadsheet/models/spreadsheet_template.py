from odoo import models, fields


class SpreadsheetTemplate(models.Model):
    _name = 'spreadsheet.template'
    _inherit = 'mixin.report.template'
    _description = "Spreadsheet Template"
    _template_field = 'xlsx_report'
    _report_type = 'xlsx'

    output_type = fields.Selection(selection_add=[
        ('xlsx', 'Spreadsheet (.xlsx)')
    ], string='Output Type', default="xlsx", required=True, ondelete={'xlsx': 'cascade'})
