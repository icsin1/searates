from odoo import models, fields, _
from .variable_object import VariableObject
from odoo.osv import expression


class AccountFinanceReport(models.Model):
    _name = 'account.finance.report'
    _inherit = 'account.finance.report.mixin'
    _description = 'Account Finance Report'

    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company')
    country_id = fields.Many2one('res.country')

    parent_menu_id = fields.Many2one('ir.ui.menu', string='Parent Menu')
    menu_id = fields.Many2one('ir.ui.menu', string='Report Menu')
    is_expanded = fields.Boolean()

    section_ids = fields.One2many('account.finance.report.section', 'report_id', 'Sections')

    def get_title(self):
        return self and self.name or self._description

    def _get_date_value_for_single(self, today, period_type, period_filter, date_options, **kwargs):
        date_from, date_to = super()._get_date_value_for_single(today, period_type, period_filter, date_options, **kwargs)
        if date_options.get('mode') == "range":
            return date_from, date_to
        return False, date_to

    def _get_header_domains(self, options, date_scope='normal', **kwargs):
        date_data = options.get('date')
        comparison = options.get('comparison', {})
        domain = self.get_date_range_domain(date_data, date_scope=date_scope)
        header_domains = [{
            'key': '{}_{}'.format(date_data.get('date_from'), date_data.get('date_to')),
            'string': date_data.get('string'),
            'date_from': date_data.get('date_from'),
            'date_to': date_data.get('date_to'),
            'domain': domain,
        }]
        periods = comparison.get('periods', [])
        if periods:
            header_domains += [{
                'key': '{}_{}'.format(period.get('date_from'), period.get('date_to')),
                'string': period.get('string'),
                'date_from': period.get('date_from'),
                'date_to': period.get('date_to'),
                'domain': self.get_date_range_domain(period, date_scope=date_scope),
            } for period in periods]

        return header_domains

    def _generate_domain(self, options, **kwargs):
        date_from, date_to = self._get_dates_range(options, **kwargs)
        # FIXME: With option
        domain = [('parent_state', '=', 'posted')]
        if date_from:
            domain = expression.AND([domain, [('date', '>=', date_from)]])
        if date_to:
            domain = expression.AND([domain, [('date', '<=', date_to)]])
        if options.get('analytic_account_ids'):
            domain = expression.AND([domain, [('analytic_account_id', 'in', options.get('analytic_account_ids'))]])
        return domain

    def _generate_periods(self, date_filter, comp_filter, date_from, date_to, period_type, period_number):
        if not date_from:
            date_from = fields.Date.start_of(fields.Date.today(), 'month')
        return super()._generate_periods(date_filter, comp_filter, date_from, date_to, period_type, period_number)

    def _get_options(self, options, **kwargs):
        options = super()._get_options(options, **kwargs)
        if self.env.user.has_group('analytic.group_analytic_accounting'):
            options['filters'] = {
                'analytic_account_ids': {
                    'string': _('Analytic'),
                    'res_model': 'account.analytic.account',
                    'res_field': 'analytic_account_ids',
                    'res_ids': options.get('analytic_account_ids', [])
                }
            }
        return options

    def get_account_report_data(self, options, **kwargs):
        self.ensure_one()
        variables = {}
        options = self._get_options(options, **kwargs)
        return {
            'title': self.name,
            'attrs': {},
            'options': options,
            'sections': self._get_sections(self.section_ids, options, variables, **kwargs),
        }

    def _get_sections(self, sections, options, variables=None, **kwargs):
        section_lines = []
        for section in sections:

            # making domain with section
            section_domain = section._get_domain()

            # Computing children first so that formula can be applied on parent
            children = self._get_sections(section.child_ids, options, variables, **kwargs)

            values = {}
            # Checking for all grouping year
            header_domains = self._get_header_domains(options, date_scope=section.date_scope, **kwargs)
            for header_domain in header_domains:
                header_Key = header_domain.get("key")
                column_domain = header_domain.get('domain', []) + section_domain
                analytic_domain = []
                if options.get('analytic_account_ids'):
                    analytic_domain = [('analytic_account_id', 'in', options.get('analytic_account_ids'))]
                column_domain += analytic_domain
                header_value_list = self._get_account_values(column_domain, ['balance:sum'], ['company_id'])
                header_value = header_value_list and header_value_list[0].get('balance', 0) or 0
                header_variables = variables.get(header_Key, VariableObject())
                header_variables['sum'] = header_value

                if section.section_id:
                    # FIXME: this should be dynamically loaded from other section of report
                    header_variables[section.section_id.code] = 0

                computed_value = section._compute_value(header_value, header_variables)
                header_variables[section.code] = computed_value
                # Resetting computed value
                values[header_domain.get('string')] = (computed_value, self._format_currency(computed_value))
                variables[header_Key] = header_variables

            section_lines.append({
                'id': section.id,
                'title': section.name,
                'code': section.code,
                'level': section.level,
                'group_by': section.group_by,
                'children': children,
                'values': self._generate_section_values(section, header_domains, values, options, **kwargs)
            })
        return self.get_sorted(options, section_lines, True)

    def _generate_section_values(self, section, header_domains, values, options, **kwargs):
        return values

    def _get_values(self, parent, options, section, group):
        computed_value = section._compute_value(group.get('balance'), VariableObject({'sum': group.get('balance', 0)}))
        if self.allow_comparison and options.get('comparison') and options.get('comparison').get('periods'):
            section_domain = section._get_domain()
            periods = options.get('comparison').get('periods')
            result = {}
            main_period = options.get('date').get('string')
            for key in parent.get('values').keys():
                if key == main_period:
                    result[key] = (computed_value, self._format_currency(computed_value))
                else:
                    period = list(filter(lambda p: p.get('string') == key, periods))
                    if period:
                        period = period[0]
                        data_domain = section_domain + self.get_date_range_domain(period) + [('account_id', '=', group.get('account_id')[0])]
                        move_line_ids = self._get_account_moves(data_domain)
                        computed_value = section._compute_value(sum(move_line_ids.mapped('balance')), VariableObject({'sum': sum(move_line_ids.mapped('balance'))}))
                        result[key] = (computed_value, self._format_currency(computed_value))
            return result
        else:
            return {key: (computed_value, self._format_currency(computed_value)) for key in parent.get('values').keys()}

    def get_account_report_section_data(self, parent, options, **kwargs):
        records = []
        section = self.env['account.finance.report.section'].sudo().browse(parent.get('id'))
        section_domain = section._get_domain()
        data_domain = section_domain + self._generate_domain(options, **kwargs)
        groups = self._get_account_values(data_domain, ['balance:sum'], ['account_id'])
        for group in groups:
            account_id, account_name = group.get('account_id') or (None, None)
            records.append({
                'id': account_id,
                'title': str(account_name),
                'code': account_id,
                'type': 'account',
                'level': 4,
                'row_class': 'text-info',
                'group_by': False,
                'values': self._get_values(parent, options, section, group)
            })
        return self.get_sorted(options, records, True)

    def _get_buttons(self, options, **kwargs):
        if self.is_expanded:
            return [
                {
                    'name': "PDF",
                    'primary': True,
                    'more': [
                        {
                            'name': "Summary",
                            'action': "action_print_report_pdf_summary",
                        },
                        {
                            'action': "action_print_report_pdf_detailed",
                            'name': "Detailed"
                        }
                    ]
                },
                {
                    'name': "Excel",
                    'primary': True,
                    'more': [
                        {
                            'action': "action_print_report_xlsx_summary",
                            'name': 'Summary'
                        },
                        {
                            'action': "action_print_report_xlsx_detailed",
                            'name': "Detailed",
                        }
                    ]
                },
                {
                    'action': "action_print_report_send_mail",
                    'name': "Send by Email",
                }
            ]

        else:
            return [
                {
                    'name': "PDF",
                    'action': "action_print_report_pdf_summary",
                    'primary': True,
                },
                {
                    'name': "Excel",
                    'primary': True,
                    'action': "action_print_report_xlsx_summary",
                },
                {
                    'action': "action_print_report_send_mail",
                    'name': "Send by Email",
                }
            ]

    def get_report_filename(self, options):
        dates = options.get('date', {})
        period = '_(' + dates.get('string') + ')'
        return self.get_title().lower().replace(' ', '_') + period

    def get_date_range_domain(self, date_data, date_scope='normal'):
        domain = [('parent_state', '=', 'posted')]
        date_from = date_data.get('date_from')
        date_to = date_data.get('date_to')
        if date_scope == 'from_begin':
            date_from = False
        elif date_scope == 'from_fiscal_year':
            today = fields.Date().today()
            if isinstance(date_to, str):
                date_to = fields.Date.from_string(date_to)
            l_date_from, l_date_to = self._get_date_value_for_range(date_to, 'today', 'this_year', {})
            date_from = l_date_from
            date_to = l_date_to
            # We are not considering future date if fiscal year is asked
            if date_to > today:
                date_to = today

        if (self.has_date_range or date_scope in ('from_fiscal_year')) and not date_scope == 'from_begin':
            domain += [('date', '>=', date_from), ('date', '<=', date_to)]
        else:
            domain += [('date', '<=', date_to)]
        return domain
