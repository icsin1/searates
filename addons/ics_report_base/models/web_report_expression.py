from odoo import models, fields
from odoo.osv import expression


class WebReportLineExpression(models.Model):
    _name = 'web.report.expression'
    _inherit = 'mixin.base.report.expression'
    _description = 'Web Report Column'

    web_report_line_id = fields.Many2one('web.report.line', required=True, ondelete='cascade')
    web_report_id = fields.Many2one('web.report', related='web_report_line_id.web_report_id', store=True)
    model_id = fields.Many2one('ir.model', related='web_report_id.model_id', store=True)
    group_by_field_id = fields.Many2one('ir.model.fields', domain="[('model_id', '=', model_id), ('ttype', 'in', ['float', 'integer', 'monetary'])]", string='Grouping Field')

    def _parse_expression_value(self, variables, value, root_domain=[], report_group={}):
        self.ensure_one()

        engine_method = f'_process_engine_{self.computation_engine}'
        if hasattr(self, engine_method):
            return getattr(self, engine_method)(variables, value, root_domain, report_group=report_group)

        return value

    def _parse_display_value(self, record, value, variables={}, report_group={}):
        self.ensure_one()

        ttype = self.value_type
        field = None
        if self.computation_engine == 'field':
            Model = self.env[self.web_report_id.model_name].sudo()
            model_fields = Model._fields
            field = model_fields.get(self.name)
            if not self.value_type:
                ttype = field.type

        parse_value = '_parse_field_{}'.format(ttype)
        if hasattr(self, parse_value):
            return getattr(self, parse_value)(record, value, field, variables, report_group=report_group)
        return value

    def _process_engine_field(self, variables, value, root_domain, report_group={}):
        return value

    def _process_engine_domain(self, variables, domain, root_domain, report_group={}):
        domain = expression.AND([domain or [], root_domain])
        date_period = report_group.get('group_period', {})
        if date_period:
            domain += self._get_date_range_domain(date_period, self.date_scope)
        groups = self.env[self.web_report_id.model_name].read_group(domain, [self.group_by_field_id.name], [])
        value = False
        if groups and groups[0].get('__count', 0) > 0:
            value = groups[0].get(self.group_by_field_id.name, False)
        return value

    def _get_date_range_domain(self, date_data, date_scope='normal'):
        """ Method utilized for computing date as per date scope defined on the expression
            currently we are supporting
            1. from_begin: which compute the date range from initial to current active date (to date selected)
            2. from_begin_period: which compute the date range from initial to selected range date from - 1 day which
                will be the last date of previous period
            3. from_fiscal_year: which will validate accordingly selected dates range fiscal year

            Here, if mode is range, then start to end date will be consider based on possible value computation
            for from_begin and from_begin_period there will be no date_from used as from_begin need to compute
            value from the start to selected period
        """
        domain = []
        date_field = self.web_report_id.date_field.name
        mode_date_range = self.web_report_id.filter_date_type == 'date_range'

        date_from = date_data.get('date_from') if mode_date_range else None
        date_to = date_data.get('date_to')

        if date_scope == 'from_begin':
            date_from = False

        elif date_scope == 'from_begin_period':
            computed_date_to = fields.Date.subtract(fields.Date.from_string(date_from or date_to), days=1)
            date_to = computed_date_to.strftime('%Y-%m-%d')
            date_from = None

        elif date_scope == 'from_fiscal_year':
            f_date_from, f_date_to = self.web_report_id._get_date_value_for_range(date_from, 'today', 'this_year', {})
            date_from = f_date_from

        elif date_scope == 'from_begin_fiscal_year':
            f_date_from, f_date_to = self.web_report_id._get_date_value_for_range(date_from, 'today', 'this_year', {})
            computed_date_to = fields.Date.subtract(fields.Date.from_string(f_date_from), days=1)
            date_from = None
            date_to = computed_date_to.strftime('%Y-%m-%d')

        domain = [(date_field, '<=', date_to)]
        if date_from:
            domain.append((date_field, '>=', date_from))
        return domain
