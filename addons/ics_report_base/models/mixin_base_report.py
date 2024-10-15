import ast
import logging
import traceback
import base64
import odoo
import datetime
from odoo import models, fields, api, tools, _
from odoo.tools import date_utils
from odoo.tools.misc import format_date
from odoo.exceptions import AccessDenied, ValidationError
from odoo.tools.safe_eval import safe_eval, test_python_expr
from odoo.tools.float_utils import float_compare
from pytz import timezone

_logger = logging.getLogger(__name__)

try:
    from num2words import num2words
except ImportError:
    _logger.warning("The num2words python library is not installed, amount-to-text features won't be fully available.")
    num2words = None

BUTTON_TYPE_LABELS = {
    'pdf': _('PDF'),
    'excel': _('Excel'),
    'csv': _('CSV'),
    'other': _("Other")
}


class BaseReport(models.AbstractModel):
    _name = 'mixin.base.report'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Base Report'

    name = fields.Char(required=True, string='Report Name')
    model_id = fields.Many2one('ir.model', required=True, ondelete='cascade')
    model_name = fields.Char(related='model_id.model', store=True, string='Model Name')
    active = fields.Boolean(default=True)
    data_match_domain = fields.Text(default="[]")
    default_opening_date = fields.Selection([
        ('this_year', 'This Year'),
        ('this_quarter', 'This Quarter'),
        ('this_month', 'This Month'),
        ('today', 'Today'),
        ('last_year', 'Last Year'),
        ('last_quarter', 'Last Quarter'),
        ('last_month', 'Last Month')
    ])

    # Filters
    filter_multi_company = fields.Selection([
        ('disabled', 'Disabled'),
        ('selector', 'Company Selector')
    ], default='disabled', required=True)
    filter_date_type = fields.Selection([
        ('disabled', 'Disabled'),
        ('as_on_today', 'As On Today'),
        ('date_range', 'Date Range')
    ], default='disabled', required=True)
    date_field = fields.Many2one('ir.model.fields', domain="[('model_id', '=', model_id), ('ttype', 'in', ['date', 'datetime'])]")
    filter_unfold_all = fields.Boolean(default=True)
    filter_comparison = fields.Boolean(default=False)

    # Customer Report Handler
    report_handler_model_id = fields.Many2one('ir.model', ondelete='cascade')
    report_handler_model_name = fields.Char(related='report_handler_model_id.model', store=True)
    # Custom Report expressions
    enable_custom_report_export = fields.Boolean(default=False, string='Custom Output Reports?')
    enable_report_handler_code = fields.Boolean(default=False)
    report_handler_python_code = fields.Text(default="""# Available variables:
#  - env: Environment on which the spec is triggered
#  - model: Property Model of the record on which computation is started; is a void recordset
#  - time, datetime, dateutil, timezone: useful Python libraries
#  - float_compare: Function to compare floats based on specific precisions
#  - web_report: web report record set
#  - report_line:dict {web_report,web_report_line,record,record_domain,options,group_by,sub_group_by}
#  - _kwargs: extra kwargs
#  - log: log(message, level='info'): logging function to record debug information in ir.logging table
#  - UserError: Warning Exception to use with raise
# To return an result, assign: result = {...}
result = {}
""")

    report_export_content = fields.Binary()
    report_export_filename = fields.Char()

    @api.constrains('report_handler_python_code')
    def _check_report_handler_python_code(self):
        for report in self.sudo().filtered('report_handler_python_code'):
            msg = test_python_expr(expr=report.report_handler_python_code.strip(), mode="exec")
            if msg:
                raise ValidationError(msg)

    @api.model
    def _get_eval_context(self, web_report=None):
        """ evaluation context to pass to safe_eval """
        def log(message, level="info"):
            with self.pool.cursor() as cr:
                cr.execute("""
                    INSERT INTO ir_logging(create_date, create_uid, type, dbname, name, level, message, path, line, func)
                    VALUES (NOW() at time zone 'UTC', %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (self.env.uid, 'server', self._cr.dbname, __name__, level, message, "web_report", web_report.id, web_report.name))

        def _num2words(number, lang='en'):
            if num2words is None:
                return ""
            try:
                return num2words(number, lang=lang).title()
            except NotImplementedError:
                return num2words(number, lang='en').title()

        return {
            'uid': self._uid,
            'user': self.env.user,
            'time': tools.safe_eval.time,
            'datetime': tools.safe_eval.datetime,
            'dateutil': tools.safe_eval.dateutil,
            'timezone': timezone,
            'float_compare': float_compare,
            # orm
            'env': self.env,
            'model': self.env[self.model_name],
            # Exceptions
            'Warning': odoo.exceptions.Warning,
            'UserError': odoo.exceptions.UserError,
            # helpers
            'log': log,
            'num2words': _num2words,
            'web_report': self
        }

    def _run_python_code(self, eval_context):
        safe_eval(self.report_handler_python_code.strip(), eval_context, mode="exec", nocopy=True)  # nocopy allows to return 'result'
        return eval_context.get('result')

    def _compute_handler_code(self, report_line, **kwargs):
        self.ensure_one()
        eval_context = self._get_eval_context(self)
        eval_context['report_line'] = report_line
        eval_context['_kwargs'] = kwargs
        result = False
        try:
            result = self._run_python_code(eval_context)
        except Exception:
            _logger.error(traceback.format_exc())
        return result

    def _get_report_handler(self):
        self.ensure_one()
        return None if not self.report_handler_model_id else self.env[self.report_handler_model_name]

    def _get_period_type(self, filter_type):
        if filter_type == 'custom':
            return 'custom'
        if not filter_type == 'today':
            return filter_type.split("_")[1]
        return filter_type

    def _get_fiscal_year_dates(self, date):
        dates = self.env.company.compute_fiscalyear_dates(date)
        return dates.get('date_from'), dates.get('date_to')

    def _get_date_value_for_single(self, today, period_type, period_filter, date_options, **kwargs):
        date_from = fields.Date.start_of(today, 'month')
        date_to = False

        # For today it will start from first date of fiscal year
        if period_filter == 'today':
            date_from, date_to = self._get_fiscal_year_dates(date_from)
        elif period_filter == 'last_month':
            date_from = fields.Date.subtract(date_from, months=1)
        elif period_filter == 'last_quarter':
            # Getting current quarter and generating last quarter date start
            q_date_from, q_date_to = date_utils.get_quarter(date_from)
            # moving 3 month back from quarter start date
            date_from = fields.Date.subtract(q_date_from, months=3)
        elif period_filter == 'last_year':
            fy_date_from, fy_date_to = self._get_fiscal_year_dates(date_from)
            # going back for 1 day and getting fiscal year dates
            date_from, date_to = self._get_fiscal_year_dates(fields.Date.subtract(fy_date_from, days=1))
        elif period_filter == 'custom':
            date_to = fields.Date.from_string(date_options.get('date_to'))
            date_from = fields.Date.from_string(date_options.get('date_from'))

        if period_filter != 'custom' and date_to and date_to > fields.Date.today():
            date_to = fields.Date.today()
        if not date_to:
            # Based on date from and period type generating end date
            date_to = fields.Date.end_of(date_from, 'month' if period_type == 'today' else period_type)

        return date_from, date_to

    def _get_date_value_for_range(self, today, period_type, period_filter, date_options, **kwargs):
        if 'last_' in period_filter:
            return self._get_date_value_for_single(today, period_type, period_filter, date_options, **kwargs)

        if isinstance(today, str):
            today = fields.Date.from_string(today)

        date_from = fields.Date.start_of(today, 'month')

        if period_filter == 'this_quarter':
            # Getting current quarter and generating last quarter date start
            date_from, date_to = date_utils.get_quarter(date_from)
        elif period_filter == 'this_year':
            date_from, date_to = self._get_fiscal_year_dates(date_from)
        elif period_filter == 'custom':
            date_to = fields.Date.from_string(date_options.get('date_to'))
            date_from = fields.Date.from_string(date_options.get('date_from'))
        else:
            # Based on date from and period type generating end date
            date_to = fields.Date.end_of(date_from, 'month' if period_type == 'today' else period_type)

        return date_from, date_to

    def _get_date_values(self, date_options, **kwargs):
        range_mode = date_options.get('mode', 'range' if self.filter_date_type == 'date_range' else 'single')
        period_filter = date_options.get("filter", 'today')
        period_type = date_options.get('period_type', "month" if self.filter_date_type == 'date_range' else 'today')
        date_from, date_to = False, False
        today = fields.Date().today()

        date_values_method = '_get_date_value_for_{}'.format(range_mode)
        if hasattr(self, date_values_method):
            date_from, date_to = getattr(self, date_values_method)(today, period_type, period_filter, date_options, **kwargs)

        return date_from, date_to

    def _get_dates_range(self, options, **kwargs):
        dates = options.get('filter_date_options', {})
        date_to = dates.get('date_to', fields.Date().today())
        date_from = dates.get('date_from', fields.Date.start_of(fields.Date.from_string(date_to), 'year'))
        return date_from, date_to

    def _get_filter_string(self, date_from, date_to, period_filter):
        if '_month' in period_filter:
            return date_to.strftime('%B %Y')
        elif '_quarter' in period_filter:
            return _('Q{} {}').format(date_utils.get_quarter_number(date_to), date_to.strftime('%Y'))
        elif '_year' in period_filter:
            fiscal_date_from, fiscal_date_to = self._get_fiscal_year_dates(date_from)
            year_string = fiscal_date_from.strftime('%Y')
            if fiscal_date_to.year != fiscal_date_from.year:
                year_string = _("FY {} - {}").format(year_string, fiscal_date_to.strftime('%Y'))
            return year_string
        elif 'custom' in period_filter:
            return _(f'From: {format_date(self.env, date_from)} to: {format_date(self.env, date_to)}')
        return date_to.strftime('%Y')

    def _get_options_dates(self, options, **kwargs):
        date_options = options.get('filter_date_options', {})
        default_filter = date_options.get('filter', self.default_opening_date)
        default_mode = 'range' if self.filter_date_type == 'date_range' else 'single'
        date_options = {
            'filter': default_filter,
            'mode': default_mode,
            **date_options,  # Overriding options
            'period_type': self._get_period_type(date_options.get('filter', default_filter)),
            'date_field': self.date_field.name
        }
        date_from, date_to = self._get_date_values(date_options, **kwargs)
        date_options.update({
            'date_from': date_from,
            'date_to': date_to,
            'string': self._get_filter_string(
                date_from, date_to, date_options.get('filter', default_filter)
            ) if self.filter_date_type == 'date_range' else _('As of {}').format(format_date(self.env, date_to))
        })
        return date_options

    def _generate_periods(self, date_filter, comp_filter, date_from, date_to, period_type, period_number):
        periods = []
        for period_n in range(period_number):
            p_date_from, p_date_end = False, False
            if comp_filter == 'previous_period':
                if period_type == 'year':
                    fiscal_date_from, fiscal_date_to = self._get_fiscal_year_dates(date_from)
                    p_date_from = fields.Date.subtract(fiscal_date_from, years=1)
                    p_date_end = fields.Date.subtract(fiscal_date_to, years=1)
                elif period_type == 'month':
                    p_date_from = fields.Date.subtract(date_from, months=1)
                    p_date_end = fields.Date.subtract(date_to, months=1)
                elif period_type == 'quarter':
                    p_date_from = fields.Date.subtract(date_from, months=3)
                    p_date_end = fields.Date.subtract(date_to, months=3)
                periods.append({
                    'date_from': p_date_from,
                    'date_to': p_date_end,
                    'period_type': period_type,
                    'period_key': p_date_end.strftime('period_%m_%y__{}'.format(period_n)),
                    'string': self._get_filter_string(
                        p_date_from, p_date_end, date_filter
                    ) if self.filter_date_type == 'date_range' else _('As of {}').format(format_date(self.env, p_date_end))
                })
            else:
                # same_last_year
                p_date_from = fields.Date.subtract(date_from, years=1)
                p_date_end = fields.Date.subtract(date_to, years=1)
                periods.append({
                    'date_from': p_date_from,
                    'date_to': p_date_end,
                    'period_type': period_type,
                    'period_key': p_date_end.strftime('period_%m_%y__{}'.format(period_n)),
                    'string': self._get_filter_string(
                        p_date_from, p_date_end, date_filter
                    ) if self.filter_date_type == 'date_range' else _('As of {}').format(format_date(self.env, p_date_end))
                })
            date_from, date_to = p_date_from, p_date_end
        return periods

    def _get_options_comparison(self, options, **kwargs):
        date_data = options.get("filter_date_options", {})
        filter_date_from, filter_date_to = date_data.get("date_from"), date_data.get('date_to')
        date_filter = date_data.get('filter').split('_')[-1]

        comparison = options.get('filter_comparison_options', {})
        comp_filter = comparison.get('filter', 'no_comparison')
        comp_period_type = comparison.get("period_type", 'year' if date_filter == 'today' else date_filter)
        comp_number_period = comparison.get('number_period', 1)
        periods = []
        date_from, date_to = False, False
        if comp_filter != 'no_comparison' and comp_number_period >= 1:
            periods = self._generate_periods(date_data.get('filter', date_data.get('filter')), comp_filter, filter_date_from, filter_date_to, comp_period_type, comp_number_period)
            date_from, date_to = periods[0].get('date_from'), periods[0].get('date_to')

        comparison_data = {
            'filter': 'no_comparison',
            'number_period': 1,
            **options.get("filter_comparison_options", {}),
            'date_from': date_from,
            'date_to': date_to,
            'periods': periods,
        }
        display_string = 'No'
        if comparison_data.get('filter') != 'no_comparison' and date_from and date_to:
            display_string = self._get_filter_string(
                date_from, date_to, date_data.get('filter', date_data.get('filter'))
            ) if self.filter_date_type == 'date_range' else 'As of {}'.format(format_date(self.env, date_to))
        comparison_data['string'] = display_string
        return comparison_data

    def _get_custom_report_buttons(self, options, **kwargs):
        return {}

    def _get_buttons(self, options, **kwargs):
        buttons = {}
        if self.enable_custom_report_export:
            buttons += self._get_custom_report_buttons()
        else:
            has_detail_view = bool(self.line_ids.filtered(lambda line: line.group_by_fields and len(line.group_by_fields.split(',')) > 1))

            buttons.update({
                'pdf': [{
                    'name': _('PDF'),
                    'help': _('Download Summary Report'),
                    'action': 'action_print_report_pdf',
                    'primary': True
                }] + ([{
                    'name': _('Detailed'),
                    'action': 'action_print_report_pdf',
                    'help': _('Download Detailed Report'),
                    'context': {'detailed': True}
                }] if has_detail_view else []),

                'excel': [{
                    'name': _('Excel'),
                    'action': 'action_print_report_xlsx',
                    'help': _('Download Summary Report'),
                    'primary': True,
                }] + ([{
                    'name': _('Detailed'),
                    'action': 'action_print_report_xlsx',
                    'help': _('Download Detailed Report'),
                    'context': {'detailed': True}
                }] + [{
                     'name': _('Without Grouping'),
                     'action': 'action_print_report_xlsx',
                     'help': _('Download Detailed Report without Party Grouping'),
                     'context': {'without_grouping': True}
                 }] if has_detail_view else [])
            })

            # buttons += [
            #     {
            #         'name': _('PDF'),
            #         'help': _('Download Summary Report'),
            #         'action': 'action_print_report_pdf',
            #         'primary': True,
            #         'type': 'pdf',
            #         'more': [
            #             {
            #                 'name': _('Detailed'),
            #                 'action': 'action_print_report_pdf',
            #                 'help': _('Download Detailed Report'),
            #                 'context': {'detailed': True}
            #             }
            #         ] if has_detail_view else []
            #     },
            #     {
            #         'name': _('Excel'),
            #         'action': 'action_print_report_xlsx',
            #         'help': _('Download Summary Report'),
            #         'primary': True,
            #         'more': [
            #             {
            #                 'name': _('Detailed'),
            #                 'action': 'action_print_report_xlsx',
            #                 'help': _('Download Detailed Report'),
            #                 'context': {'detailed': True}
            #             }
            #         ] if has_detail_view else []
            #     },
            #     # {
            #     #     'action': "action_print_report_send_mail",
            #     #     'help': _('Send Report by Email'),
            #     #     'name': "Send by Email",
            #     # }
            # ]
        custom_handler = self._get_report_handler()
        if custom_handler is not None:
            handler_buttons = custom_handler._get_handler_buttons(self, options, **kwargs)
            for key, handler_buttons in handler_buttons.items():
                buttons.update({key: buttons.get(key, []) + handler_buttons})
        return self._to_display_button(buttons)

    def _to_display_button(self, button_data):
        button_list = []
        for key, buttons in button_data.items():
            key_buttons = list(filter(lambda btn: btn.get('primary'), buttons))
            if not key_buttons and buttons:
                buttons[0].update({'primary': True})
                key_buttons = buttons[:1]
            if key_buttons:
                key_buttons[0].update({'more': list(filter(lambda btn: not btn.get('primary'), buttons))})
            button_list += key_buttons
        return button_list

    def _get_report_filename(self, options):
        self.ensure_one()

        custom_handler = self._get_report_handler()
        if custom_handler is not None:
            return custom_handler._get_report_filename(self, options)

        period = ''
        if options.get('filter_date', False):
            dates = options.get('filter_date_options', {})
            date_to = dates.get('date_to', fields.Date().today())
            date_from = dates.get('date_from', fields.Date.start_of(fields.Date.from_string(date_to), 'year'))
            if isinstance(date_from, datetime.date):
                date_from = fields.Date.to_string(date_from)
            if isinstance(date_to, datetime.date):
                date_to = fields.Date.to_string(date_to)
            period = '_(' + date_from + ' to ' + date_to + ')'
        return self.name.lower().replace(' ', '_') + period

    def get_title(self):
        custom_handler = self._get_report_handler()
        if custom_handler is not None:
            return custom_handler._get_report_title(self)
        return self.name

    def action_call_handler_method(self, options, **kwargs):
        context = dict(self._context)
        self = self.with_context(context)
        button_context = context.get('button_context', {})
        button_action = context.get('button_action')
        custom_handler = self._get_report_handler()
        if custom_handler is not None:
            return getattr(custom_handler, button_action)(self, options, button_context, **kwargs)

    def action_print_report_pdf(self, options, **kwargs):
        context = dict(self._context)
        self = self.with_context(context)
        button_context = context.get('button_context', {})
        filename = self._get_report_filename(options)

        action = self.get_report_action(options)
        action.update({
            'data': {
                'print_report_name': filename,
                'report_model': action.get('report_res_model'),
                'report_res_id': action.get('report_res_id'),
                'model': self._name,
                'report_id': self.id,
                'options': options,
                'folded': not button_context.get('detailed', False)
            }
        })
        action['context'] = {**self.env.context, 'active_ids': self.ids, 'default_print_report_name': filename}
        return action

    def _get_objs_for_report(self, docids, data):
        # OVERRIDING EXCEL Object browser
        return self

    def _get_report_title(self, options, **kwargs):
        self.ensure_one()
        title_label = self.name
        if options.get('filter_date'):
            title_label = options.get('filter_date_options').get('string')
            mode = options.get('filter_date_options').get('mode')
            if mode == 'range':
                period = "{} to {}".format(
                    format_date(self.env, options['filter_date_options']['date_from']),
                    format_date(self.env, options['filter_date_options']['date_to'])
                ) if options.get('filter_date', False) else ''
                title_label = "{} ({})".format(title_label, period)
        return title_label

    def _add_child_rows(self, workbook, sheet, sections, data, parent_section=None, parent_row_idx=None):
        button_context = self.env.context.get('button_context', {})
        detailed_report = button_context.get('detailed', False) and not parent_section
        without_grouping = button_context.get('without_grouping', False)

        options = data.get('options', {})
        group_headers = options.get('report_header_groups', [])
        headers = options.get('headers', [])

        if not parent_section:
            # Company Header
            total_cols = len(headers) * len(group_headers)

            # Title
            sheet.merge_range(0, 0, 0, total_cols, self.get_title(), workbook.add_format({
                'bold': True,
                "border": 1,
                "align": "center",
                'bg_color': "#FFFFFF",
                'font_size': '16px'
            }))
            # Date Ranges
            title_label = self._get_report_title(options)
            sheet.merge_range(1, 0, 1, total_cols, title_label, workbook.add_format({
                'bold': True,
                "border": 1,
                "align": "center",
                'bg_color': "#FFFFFF"
            }))
            # Empty row
            sheet.merge_range(2, 0, 2, total_cols, '', workbook.add_format({
                'bold': True,
                "border": 1,
                "align": "center",
                'bg_color': "#FFFFFF"
            }))

        row_idx = 3

        for group_key, group_header in group_headers.items():
            row_idx = row_idx if not parent_row_idx else parent_row_idx
            col_idx = 0

            # First row empty
            sheet.write(row_idx, col_idx, '', workbook.add_format({'border': 1}))

            if not parent_section:
                # Headers
                for header in headers:
                    col_idx += 1
                    sheet.write(row_idx, col_idx, str(header.get('string')), workbook.add_format({
                        'bold': True,
                        'bg_color': '#c9c7c7',
                        'border': 1
                    }))
                row_idx += 1

            data_sections = sections
            if (without_grouping and not parent_section) or (not parent_section and detailed_report):
                data_sections = list(filter(lambda sec: not sec.get('group_total', False), sections))

            for section in data_sections:
                col_idx = 0
                _grouping_title = ''

                if without_grouping and parent_section:
                    _grouping_title = str(parent_section.get('title'))

                if not without_grouping or parent_section:
                    sheet.write(row_idx, col_idx, str(section.get('title')), workbook.add_format({
                        'bold': bool(not parent_section),
                        'italic': False,
                        'bg_color': '#FFFFFF',
                        'border': 1,
                        'indent': section.get('level', 1) if parent_section and not without_grouping else 0
                    }))

                    for header in headers:
                        col_idx += 1
                        value = section.get('values', {}).get(group_key, {}).get("{}_original".format(header.get('expression_label')))
                        if header.get('expression_label') == '_grouping_title' and without_grouping:
                            value = _grouping_title
                        if header.get('value_type') == 'date':
                            value = value and format_date(self.env, value) or ''
                        sheet.write(row_idx, col_idx, value or '', workbook.add_format({
                            'bold': section.get('group_total', False) or detailed_report,
                            'italic': section.get('group_total', False),
                            'bg_color': '#EBEBEB' if section.get('group_total', False) or detailed_report else '#FFFFFF',
                            'border': 1,
                        }))

                if (detailed_report or without_grouping) and not parent_section:
                    child_sections = self.get_web_report_section_data(section, options)
                    if without_grouping:
                        child_sections = list(filter(lambda sec: not sec.get('group_total', False), child_sections))
                    self._add_child_rows(workbook, sheet, child_sections, data, section, parent_row_idx=row_idx + 1 if not without_grouping else row_idx)
                    row_idx += len(child_sections) + (1 if not without_grouping else -1)
                row_idx += 1

            sheet.autofit()

    def generate_xlsx_report(self, workbook, data, objs):
        button_context = self.env.context.get('button_context', {})
        detailed_report = button_context.get('detailed', False)
        without_grouping = button_context.get('without_grouping', False)
        options = self._get_options(data.get('options', {}))
        for obj in objs:
            parent_sections = obj._get_sections(options)
            sheet = workbook.add_worksheet("{}{}".format(obj.get_title(), _(' Detailed') if (detailed_report or without_grouping) else ''))
            if without_grouping:
                headers = options.get('headers', [])
                headers.insert(0, {
                    'expression_label': '_grouping_title',
                    'hide_if_zero': False,
                    'id': False,
                    'sequence': 0,
                    'sortable': False,
                    'string': obj.line_ids and obj.line_ids[0].name or _('Group Title'),
                    'value_type': 'string'
                })
            obj._add_child_rows(workbook, sheet, parent_sections, data)

    def action_print_report_xlsx(self, options, **kwargs):
        self.ensure_one()
        excel_file, extension = self.create_xlsx_report(self.ids, {
            'options': options,
            'kwargs': kwargs
        })
        filename = self._get_report_filename(options)
        filename = '{}.{}'.format(filename, extension)
        self.write({
            'report_export_filename': filename,
            'report_export_content': base64.b64encode(excel_file)
        })

        url = '/web/content/%s/%s/%s/%s' % (self._name, self.id, 'report_export_content', self.report_export_filename)
        return {'type': 'ir.actions.act_url', 'url': url}

    def action_print_report_send_mail(self, options, **kwargs):
        raise ValidationError('Sending Email supported as of now')
        # context = dict(self._context.get('context'))
        # landscape = True if len(options.get('headers')) > 5 else False
        # context.update({'landscape': landscape})
        # self = self.with_context(context)
        # template_id = self.env['ir.model.data']._xmlid_to_res_id('ics_account_reports.finance_report_email_template', raise_if_not_found=False)
        # title = self.get_title()
        # filename = '{}.pdf'.format(title)
        # AttachmentObj = self.env['ir.attachment']
        # attachment = AttachmentObj.search([('name', '=', filename)], limit=1)
        # pdf_datas = self.get_pdf(options)

        # attachment = AttachmentObj.create({
        #     'name': filename,
        #     'datas': base64.b64encode(pdf_datas),
        #     'store_fname': filename,
        #     'res_model': self._name,
        #     'res_id': 0,
        #     'type': 'binary',
        #     'mimetype': 'application/pdf'
        # })
        # ctx = {
        #     'default_model': self._name,
        #     'default_res_id': self.id,
        #     'default_use_template': bool(template_id),
        #     'default_template_id': template_id,
        #     'custom_layout': "mail.mail_notification_light",
        #     'default_attachment_ids': attachment.ids,
        #     'subject': title,
        # }
        # return {
        #     'name': 'Report Send by Email: %s' % (title),
        #     'type': 'ir.actions.act_window',
        #     'view_mode': 'form',
        #     'res_model': 'mail.compose.message',
        #     'views': [(False, 'form')],
        #     'view_id': False,
        #     'target': 'new',
        #     'context': ctx,
        # }
        pass

    def get_report_action(self, options=False):
        return self.env["ir.actions.actions"]._for_xml_id("ics_report_base.action_generic_web_report_pdf")

    def _get_column_headers(self, options, **kwargs):
        column_headers = []
        handler = self._get_report_handler()
        for column in self.column_ids:
            column_headers.append({
                'id': column.id,
                'string': handler._get_column_label(column, options, **kwargs) if handler is not None else column.name,
                'value_type': column.value_type,
                'sortable': column.sortable,
                'hide_if_zero': column.hide_if_zero,
                'expression_label': column.expression_label,
                'sequence': column.sequence,
                'reverse': options.get('reverse'),
                'orderby': options.get('orderby')
            })
        return column_headers

    def _get_dynamic_filters(self, options, **kwargs):
        """ Sample:
            [{
                'string': "Partners",
                'res_model': 'res.partner',
                'res_field': 'partner_id',
                'res_ids': []
            }]
        """
        handler = self._get_report_handler()
        return [{
            'string': report_filter.get_name(options.get('dynamic_filter_search', {}).get(report_filter.filter_key)) if handler is None else handler._get_filter_label(
                report_filter, options, **kwargs
            ),
            'name': report_filter.name,
            'res_model': report_filter.ir_model_field_id.relation,
            'res_field': report_filter.ir_model_field_id.name,
            'filter_type': report_filter.filter_type,
            'icon': report_filter.icon or 'fa-filter',
            'filter_key': report_filter.filter_key,
            'default_value': options.get('dynamic_filter_search', {}).get(report_filter.filter_key, report_filter.get_default_value()),
            'domain': report_filter.data_domain,
            'choices': [{
                'label': choice.name,
                'choice_key': choice.choice_key,
                'choice_id': '{}_{}_{}'.format(report_filter.filter_key, choice.choice_key, choice.id),
                'is_default': choice.is_default,
            } for choice in report_filter.choice_ids],
            'res_ids': [],
            **(handler._get_filter_options(report_filter, options, **kwargs) if handler is not None else {})
        } for report_filter in self.filter_ids]

    def _get_options(self, options, **kwargs):

        # Date filter
        options['filter_date'] = bool(self.filter_date_type != 'disabled')
        if self.filter_date_type != 'disabled':
            options['filter_date_options'] = self._get_options_dates(options, **kwargs)

        options['report_header_groups'] = self._get_report_groups(options, **kwargs)

        # comparison filter
        options['filter_comparison'] = self.filter_date_type != 'disabled' and self.filter_comparison
        if self.filter_date_type != 'disabled' and self.filter_comparison:
            options['filter_comparison_options'] = self._get_options_comparison(options, **kwargs)

        # Unfold all
        options['filter_unfold_all'] = self.filter_unfold_all

        options['filter_configuration'] = self.user_has_groups('base.group_no_one')
        options['report_id'] = self.id

        # Dynamic filters
        options['filter_dynamic_filters'] = self._get_dynamic_filters(options, **kwargs)

        dynamic_filter_search_default_values = {
            dynamic_filter.get('filter_key'): dynamic_filter.get('default_value') for dynamic_filter in options['filter_dynamic_filters'] if dynamic_filter.get('filter_type') not in [
                'single_relation', 'multi_relation'
            ]
        }

        options['dynamic_filter_search'] = {
            **dynamic_filter_search_default_values,
            **options.get('dynamic_filter_search', {})
        }
        options['buttons'] = self._get_buttons(options, **kwargs)
        options['company'] = self.env.company.name
        options['company_id'] = self.env.company.id
        options['headers'] = self._get_column_headers(options, **kwargs)

        custom_handler = self._get_report_handler()
        options['show_title'] = not custom_handler._hide_title if custom_handler is not None else True
        return options

    def _get_group_domains(self, options, **kwargs):
        date_data = options.get('date')
        comparison = options.get('comparison', {})

        header_domains = [{
            'key': '{}_{}'.format(date_data.get('date_from'), date_data.get('date_to')),
            'string': date_data.get('string'),
            'date_from': date_data.get('date_from'),
            'date_to': date_data.get('date_to'),
            'domain': [('date', '>=', date_data.get('date_from')), ('date', '<=', date_data.get('date_to')), ('parent_state', '=', 'posted')]
        }]
        periods = comparison.get('periods', [])
        if periods:
            header_domains += [{
                'key': '{}_{}'.format(period.get('date_from'), period.get('date_to')),
                'string': period.get('string'),
                'date_from': period.get('date_from'),
                'date_to': period.get('date_to'),
                'domain': [('date', '>=', period.get('date_from')), ('date', '<=', period.get('date_to')), ('parent_state', '=', 'posted')]
            } for period in periods]

        return header_domains

    def _generate_initial_balance_domain(self, date_from, date_to, options, **kwargs):
        return [('date', '<', date_from)] + self._get_default_domain(options, ignore_date_domain=True, **kwargs)

    def _get_report_groups(self, options, **kwargs):
        report_groups = {}
        date_options = options.get('filter_date_options', {})
        main_group_domain = self._get_default_domain(options, **kwargs)
        date_from, date_to = self._get_dates_range(options, **kwargs)
        main_group_period = {
            'date_from': date_from,
            'date_to': date_to,
            'mode': date_options.get('mode')
        }
        if self.filter_date_type != 'disabled':
            report_groups.update({
                'main_group': {
                    'string': date_options.get('string', ''),
                    'group_period': main_group_period,
                    '__domain': main_group_domain
                }
            })
        else:
            report_groups.update({
                'main_group': {
                    'string': '',
                    'group_period': main_group_period,
                    '__domain': main_group_domain
                }
            })
        if self.filter_date_type != 'disabled' and self.filter_comparison:
            comparison_data = self._get_options_comparison(options, **kwargs)
            date_field = self.date_field.name
            if comparison_data.get('filter') != 'no_comparison':
                for group_period in comparison_data.get('periods', []):
                    period_domain = [
                        (date_field, '>=', group_period.get('date_from')),
                        (date_field, '<=', group_period.get('date_to'))
                    ] + self._get_default_domain(options, ignore_date_domain=True, **kwargs)
                    report_groups.update({
                        group_period.get('period_key'): {
                            'string': group_period.get('string'),
                            'group_period': group_period,
                            '__domain': period_domain
                        }
                    })
        return report_groups

    def _get_sections(self, options, **kwargs):
        sections = []

        # Executing custom section handler if no lines are define on report
        report_handler = self._get_report_handler()
        if not self.line_ids and report_handler is not None:
            return report_handler._get_sections(self, options, **kwargs) or []

        for line in self.line_ids:
            if report_handler is not None and report_handler._override_sections_data:
                sections += line._get_handler_sections(self, report_handler, options, **kwargs)
            else:
                sections += line._get_section_data(options, **kwargs)
        if options.get('orderby'):
            orderby_key = f"{options.get('orderby')}_original"
            group_total_items = [item for item in sections if item.get('group_total')]
            if len(sections) == len(group_total_items):
                return sorted(sections, key=lambda x: x['values']['main_group'][orderby_key], reverse=options.get('reverse'))
            sorted_items = sorted(
                (item for item in sections if not item.get('group_total')),
                key=lambda x: x['values']['main_group'][orderby_key],
                reverse=options.get('reverse')
            )
            sorted_items.extend(group_total_items)
            return sorted_items
        return sections

    def get_web_report(self, options, **kwargs):
        options = self._get_options(options, **kwargs)
        return {
            'title': self.name,
            'attrs': {},
            'options': options,
            'sections': self._get_sections(options, **kwargs),
            'buttons': []
        }

    def get_web_report_section_data(self, section, options, **kwargs):
        line = self.line_ids.filtered(lambda line: line.id == section.get('line_id'))
        report_handler = self._get_report_handler()
        if line:
            if report_handler is not None and report_handler._override_section_detail:
                return report_handler._get_section_detail_data(self, line, options, parent=section, level=section.get('level'), **kwargs)
            return line._get_section_data(options, parent_section=section, level=section.get('level'), **kwargs)
        return []

    def _get_default_domain(self, options, **kwargs):
        domain = ast.literal_eval(self.data_match_domain or '[]')
        # All Filter domain
        domain += self._filter_domain(options, **kwargs)

        handler = self._get_report_handler()
        if handler is not None:
            domain += handler._get_handler_domain(self, options, **kwargs)

        return domain

    def _filter_domain(self, options, ignore_date_domain=False, **kwargs):
        domain = []
        if self.filter_date_type != 'disabled' and not ignore_date_domain:
            date_field = self.date_field.name
            date_from, date_to = self._get_dates_range(options, **kwargs)
            domain += [(date_field, '<=', date_to)]
            if options.get('filter_date_options', {}).get('mode') == 'range':
                domain += [(date_field, '>=', date_from)]

        if self.filter_multi_company != 'disabled':
            if self.filter_multi_company == 'selector':
                domain += [('company_id', '=', self.env.company.id)]

        if options.get('dynamic_filter_search', {}):
            for filter_key, filter_value in options.get('dynamic_filter_search').items():
                domain += self._generate_filter_domain(filter_key, filter_value) if filter_value else []

        context_domain = self.env.context.get('domain')
        if context_domain:
            domain += ast.literal_eval(context_domain) if isinstance(context_domain, str) else context_domain or []
        return domain

    def _generate_filter_domain(self, filter_key, filter_value):
        data_filters = self.filter_ids.filtered(lambda filter: filter.filter_key == filter_key and filter.filter_type in ['single_relation', 'multi_relation'])
        domain = []
        for data_filter in data_filters:
            domain += [(data_filter.ir_model_field_id.name, 'in', filter_value)]
        return domain

    def action_open_report_configuration(self, options, **kwargs):
        self.ensure_one()
        if not self.user_has_groups('base.group_no_one'):
            raise AccessDenied(_('You are not allowed to access Report Configuration'))
        return {
            "type": "ir.actions.act_window",
            "name": _("Report Configuration"),
            "res_model": "web.report",
            "res_id": self.id,
            "view_mode": "form",
            "views": [(False, "form")],
            "target": "current",
            "context": {'create': 0, 'delete': 0}
        }

    @api.model
    def _generate_query_params(self, options, domain=None, **kwargs):
        domain = (domain or [])
        if not self.env.context.get('ignore_date_domain'):
            domain += self._get_default_domain(options, **kwargs)
        self.env[self.model_name].check_access_rights('read')

        query = self.env[self.model_name]._where_calc(domain)

        self.env[self.model_name]._apply_ir_rules(query)

        return query.get_sql()
