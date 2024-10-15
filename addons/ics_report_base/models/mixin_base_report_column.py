from odoo import models, fields


class BaseReportColumn(models.AbstractModel):
    _name = 'mixin.base.report.column'
    _description = 'Base Report Column'
    _order = 'sequence,name'

    name = fields.Char(required=True, string='Column Name')
    expression_label = fields.Char(required=True, string='Expression Label')
    hide_if_zero = fields.Boolean(default=False)
    value_type = fields.Selection([
        ('monetary', 'Monetary'),
        ('percentage', 'Percentage'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('date', 'Date'),
        ('datetime', 'Datetime'),
        ('boolean', 'Boolean'),
        ('string', 'String'),
        ('text', 'Text')
    ])
    sortable = fields.Boolean(default=False)
    sequence = fields.Integer(default=0)
