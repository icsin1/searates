from odoo import models, fields
from odoo.tools.misc import formatLang, get_lang, format_date


class BaseReportExpression(models.AbstractModel):
    _name = 'mixin.base.report.expression'
    _description = 'Base Report Expression'

    name = fields.Char(required=True, string='Expression Label')
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
    currency_field_name = fields.Char()
    computation_engine = fields.Selection([
        ('domain', 'Domain'),
        # ('aggregation', 'Aggregated Formula'),
        ('python_code', 'Python Code'),
        ('field', 'Field')
    ], default='domain', required=True)
    formula_expression = fields.Char(required=True)
    subformula_expression = fields.Char()
    allow_aggregate = fields.Boolean(default=False)
    date_scope = fields.Selection([
        ('from_begin', 'From Beginning to Date'),
        ('from_begin_period', 'From Beginning of the Period'),
        ('from_fiscal_year', 'From Fiscal year'),
        ('from_begin_fiscal_year', 'From Beginning Of The Fiscal year'),
        ('normal', 'As Selected Dates')
    ], default='normal', required=True, help="""
1. From Beginning to Date: which compute the date range from initial to current active date (to date selected)
2. From Beginning of the Period: which compute the date range from initial to selected range date from - 1 day which
    will be the last date of previous period
3. From Fiscal year: which will validate accordingly selected dates range fiscal year
4. As Selected Dates: selected date range / period forced to compute which is default
""")

    def _parse_expression_value(self, value, field, report_group={}):
        self.ensure_one()
        return value

    def _parse_field_monetary(self, record, record_value, field, variables, report_group={}):
        currency = self.env.company.currency_id
        currency_field = (field and field.currency_field) or self.currency_field_name
        if currency_field:
            currency_id = record.get(currency_field, variables.get(currency_field, [0, False]))
            if isinstance(currency_id, int):
                currency_id = (currency_id, False)
            if currency_id and isinstance(currency_id, tuple) and currency_id[0]:
                currency = self.env['res.currency'].sudo().browse(currency_id[0])
        return formatLang(self.env, record_value or 0, currency_obj=currency)

    def _parse_field_float(self, record, record_value, field, variables, report_group={}):
        return round(record_value or 0, 2)

    def _parse_field_percentage(self, record, record_value, field, variables, report_group={}):
        return "{} %".format(self._parse_field_float((record_value or 0) * 100))

    def _parse_field_date(self, record, date_obj, field, variables, report_group={}):
        lang = get_lang(self.env)
        if date_obj:
            return format_date(self.env, date_obj, lang_code=lang.code, date_format=False)
        return False
