import ast
from odoo import models, fields
from odoo.tools.safe_eval import safe_eval


class AccountFinanceReportSection(models.Model):
    _name = 'account.finance.report.section'
    _description = 'Account Finance Report Section'
    _order = 'sequence'

    report_id = fields.Many2one('account.finance.report', ondelete='cascade')
    name = fields.Char(required=True, string='Section Name')
    code = fields.Char(required=True, string='Section Code')
    sequence = fields.Integer(default=1)
    date_scope = fields.Selection([
        ('from_begin', 'From Beginning'),
        ('from_fiscal_year', 'From Fiscal year'),
        ('normal', 'As Selected Dates')
    ], default='normal', required=True)

    computation_formula = fields.Char()

    # filters and domain
    group_by = fields.Char(string='Group by (Fields)')
    data_domain = fields.Char()
    validation_domain = fields.Char()

    # UI
    level = fields.Integer(default=0)

    # Parent & child mapping
    parent_id = fields.Many2one('account.finance.report.section', ondelete='cascade')
    child_ids = fields.One2many('account.finance.report.section', 'parent_id', string='Sub Sections')
    # Related report section
    section_id = fields.Many2one('account.finance.report.section')

    _sql_constraints = [
        ('name_unique', 'unique(report_id,parent_id,code)', 'The Report Code need to be unique')
    ]

    def _get_domain(self):
        self.ensure_one()
        domain = []
        if self.validation_domain:
            domain += ast.literal_eval(self.validation_domain)
        if self.data_domain:
            domain += ast.literal_eval(self.data_domain)
        return domain

    def _compute_value(self, amount, variables):
        self.ensure_one()
        if self.computation_formula:
            formula = "result = {}".format(self.computation_formula)
            safe_eval(formula, variables, mode='exec', nocopy=True)
            amount = variables.result

        # Removing builtins variables for clean dict
        if '__builtins__' in variables:
            del variables['__builtins__']

        return amount
