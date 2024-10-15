# -*- coding: utf-8 -*-
import base64
import io
import xlsxwriter
import json

from datetime import datetime

from odoo import models, fields, _
from odoo.tools import date_utils
from odoo.tools.misc import formatLang, format_date, get_lang, format_datetime
from odoo.addons.web.controllers.main import clean_action
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class FinanceReportMixin(models.AbstractModel):
    _name = 'account.finance.report.mixin'
    _description = 'Account Finance Report Mixin'

    # Report Settings
    has_date_range = fields.Boolean(default=False, string='Based on date ranges')
    is_tax_report = fields.Boolean(default=False, string='Is Tax Report?')

    # Filters settings
    allow_comparison = fields.Boolean(default=False)
    allow_filter_by_journal = fields.Boolean(default=False)

    def get_title(self):
        return _('Finance Report')

    def get_account_report_data(self, options, **kwargs):
        options = self._get_options(options, **kwargs)
        return {
            'title': self.get_title(),
            'attrs': {},
            'options': options,
            'sections': []
        }

    def get_sorted(self, options, sections, is_line=False):
        if not options.get('sortable'):
            return sections

        if not options.get('orderby'):
            options['orderby'] = '#'

        def sort(section):
            try:
                if options.get('orderby') == '#':
                    value = section.get('title', {})
                else:
                    value = section.get('values', {}).get(options.get('orderby'))
                if value == '':
                    value = '0'

                if isinstance(value, tuple):
                    return value[0]
                elif isinstance(value, str):
                    try:
                        return datetime.strptime(value, date_format)
                    except ValueError:
                        return value
                    return value
                else:
                    return value
            except Exception:
                return section.get('values', {}).get(options.get('orderby'))
        try:
            date_format = get_lang(self.env).date_format
            if is_line:
                return sorted(sections, key=sort, reverse=options.get('reverse', False))

            sorted_sections = sorted(filter(lambda x: x['group_by'], sections), key=sort, reverse=options.get('reverse', False))
            return sorted_sections + list(filter(lambda x: not x['group_by'], sections))
        except Exception:
            return sections

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
        if not date_to:
            # Based on date from and period type generating end date
            date_to = fields.Date.end_of(date_from, 'month' if period_type == 'today' else period_type)

        return date_from, date_to

    def _get_date_value_for_range(self, today, period_type, period_filter, date_options, **kwargs):
        if 'last_' in period_filter:
            return self._get_date_value_for_single(today, period_type, period_filter, date_options, **kwargs)

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
        range_mode = date_options.get('mode', 'range' if self.has_date_range else 'single')
        period_filter = date_options.get("filter", 'today')
        period_type = date_options.get('period_type', "month" if self.has_date_range else 'today')
        date_from, date_to = False, False
        today = fields.Date().today()

        date_values_method = '_get_date_value_for_{}'.format(range_mode)
        if hasattr(self, date_values_method):
            date_from, date_to = getattr(self, date_values_method)(today, period_type, period_filter, date_options, **kwargs)

        if date_to > today:
            date_to = today

        return date_from, date_to

    def _get_dates_range(self, options, **kwargs):
        dates = options.get('date', {})
        date_to = dates.get('date_to', fields.Date().today())
        date_from = dates.get('date_from', fields.Date.start_of(fields.Date.from_string(date_to), 'year'))
        return date_from, date_to

    def _generate_initial_balance_domain(self, options, **kwargs):
        date_from, date_to = self._get_dates_range(options, **kwargs)

        domain = [('date', '<', date_from)]
        # FIXME: With option
        domain += [('parent_state', '=', 'posted')]
        return domain

    def _generate_domain(self, options, **kwargs):
        date_from, date_to = self._get_dates_range(options, **kwargs)
        domain = [('date', '>=', date_from), ('date', '<=', date_to)]
        # FIXME: With option
        domain += [('parent_state', '=', 'posted')]
        return domain

    def _get_period_type(self, filter_type):
        if filter_type == 'custom':
            return 'custom'
        if not filter_type == 'today':
            return filter_type.split("_")[1]
        return filter_type

    def _get_filter_string(self, date_from, date_to, period_filter):
        if '_month' in period_filter:
            return date_to.strftime('%B %Y')
        elif '_quarter' in period_filter:
            return 'Q{} {}'.format(date_utils.get_quarter_number(date_to), date_to.strftime('%Y'))
        elif '_year' in period_filter:
            fiscal_date_from, fiscal_date_to = self._get_fiscal_year_dates(date_from)
            year_string = fiscal_date_from.strftime('%Y')
            if fiscal_date_to.year != fiscal_date_from.year:
                year_string = "{} - {}".format(year_string, fiscal_date_to.strftime('%Y'))
            return year_string
        elif 'custom' in period_filter:
            return f'From: {format_date(self.env, date_from)} - to: {format_date(self.env, date_to)}'
        return date_to.strftime('%Y')

    def convert_date_to_lang_date(self, default_date):
        lang = get_lang(self.env, self.env.user.lang)
        date_format = lang.date_format
        if default_date and type(default_date) is str:
            return datetime.strptime(default_date, DEFAULT_SERVER_DATE_FORMAT).strftime(date_format)
        elif default_date:
            return default_date.strftime(date_format)

    def _get_buttons(self, options, **kwargs):
        return [
            {
                'name': "PDF",
                'action': "action_print_report_pdf_summary",
                'primary': True,
                # USE THIS OPTION IF YOU NEED MORE REPORTS UNDER SAME BUTTON
                # 'more': [
                #     {
                #         'name': "Summary",
                #         'action': "action_print_report_pdf_summary",
                #     },
                #     {
                #         'action': "action_print_report_pdf_detailed",
                #         'name': "Detailed"
                #     }
                # ]
            },
            {
                'name': "Excel",
                'primary': True,
                'action': "action_print_report_xlsx_summary",
                # USE THIS OPTION IF YOU NEED MORE REPORTS UNDER SAME BUTTON
                # 'more': [
                #     {
                #         'action': "action_print_report_xlsx_summary",
                #         'name': 'Summary'
                #     },
                #     {
                #         'action': "action_print_report_xlsx_detailed",
                #         'name': "Detailed",
                #     }
                # ]
            },
            {
                'action': "action_print_report_send_mail",
                'name': "Send by Email",
            }
        ]

    def _get_options_dates(self, options, **kwargs):
        date_options = options.get('date', {})
        default_filter = 'this_month' if self.has_date_range else 'today'
        default_mode = 'range' if self.has_date_range else 'single'
        date_options = {
            'filter': default_filter,
            'mode': default_mode,
            **date_options,  # Overriding options
            'period_type': self._get_period_type(date_options.get('filter', default_filter)),
        }
        date_from, date_to = self._get_date_values(date_options, **kwargs)
        date_options.update({
            'date_from': date_from,
            'date_to': date_to,
            'string': self._get_filter_string(date_from, date_to, date_options.get('filter', default_filter)) if self.has_date_range else 'As of {}'.format(format_date(self.env, date_to)),
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
                    'string': self._get_filter_string(
                        p_date_from, p_date_end, date_filter
                    ) if self.has_date_range else 'As of {}'.format(format_date(self.env, p_date_end))
                })
            else:
                # same_last_year
                p_date_from = fields.Date.subtract(date_from, years=1)
                p_date_end = fields.Date.subtract(date_to, years=1)
                periods.append({
                    'date_from': p_date_from,
                    'date_to': p_date_end,
                    'period_type': period_type,
                    'string': self._get_filter_string(
                        p_date_from, p_date_end, date_filter
                    ) if self.has_date_range else 'As of {}'.format(format_date(self.env, p_date_end))
                })
            date_from, date_to = p_date_from, p_date_end
        return periods

    def _get_options_comparison(self, options, **kwargs):

        date_data = options.get("date")
        filter_date_from, filter_date_to = date_data.get("date_from"), date_data.get('date_to')
        date_filter = date_data.get('filter').split('_')[-1]

        comparison = options.get('comparison', {})
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
            **options.get("comparison", {}),
            'date_from': date_from,
            'date_to': date_to,
            'periods': periods,
        }
        display_string = ''
        if comparison_data.get('filter') != 'no_comparison' and date_from and date_to:
            display_string = self._get_filter_string(
                date_from, date_to, date_data.get('filter', date_data.get('filter'))
            ) if self.has_date_range else 'As of {}'.format(format_date(self.env, date_to))
        comparison_data['string'] = display_string
        return comparison_data

    def _get_options(self, options, **kwargs):
        # Keep date at
        options['date'] = self._get_options_dates(options, **kwargs)
        options['buttons'] = self._get_buttons(options, **kwargs)
        options['company'] = self.env.company.name
        options['is_tax_report'] = self.is_tax_report
        options['tax_reports'] = self._get_tax_reports() if self.is_tax_report else []
        options['active_tax_report'] = options.get('active_tax_report', list(options['tax_reports'].values())[0] if self.is_tax_report and options.get('tax_reports') else False)

        if self.allow_comparison:
            options['comparison'] = self._get_options_comparison(options, **kwargs)

        options['headers'] = self._get_column_headers(options, **kwargs)
        options['headers_properties'] = self._get_column_headers_properties(options, **kwargs)
        return options

    def _get_tax_reports(self):
        reports = self.env['account.tax.report'].sudo().search([('country_id', '=', self.env.company.country_id.id)])
        return {report.id: {
            'id': report.id,
            'name': '{} ({})'.format(report.name, report.country_id.code.upper()),
            'country_id': (report.country_id.id, report.country_id.name)
        } for report in reports}

    def _get_header_domains(self, options, **kwargs):
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

    def _get_column_headers(self, options, **kwargs):
        date_data = options.get('date')
        comparison = options.get('comparison', {})

        headers = [date_data.get('string')]
        periods = comparison.get('periods', [])
        if periods:
            headers = headers + [period.get('string') for period in periods]

        return headers

    def _get_column_headers_properties(self, options, *kwargs):
        return {}

    def _get_account_moves(self, domain, count=False):
        return self.env['account.move.line'].search(domain, count=count)

    def _get_account_values(self, domain, fields, group_by_fields, limit=None):
        return self.env['account.move.line'].read_group(domain, fields, group_by_fields, limit=limit)

    def _format_currency(self, amount, currency=None):
        return formatLang(self.env, amount, currency_obj=currency or self.env.company.currency_id)

    def get_report_action(self, options=False):
        return self.env.ref('ics_account_reports.action_generic_report_account')

    def get_pdf(self, options):
        context = self._context.copy()
        landscape = True if len(options.get('headers')) > 5 else False
        context.update({'landscape': landscape})
        self = self.with_context(context)
        pdf_datas = self.get_report_action(options)._render_qweb_pdf(self, data={'options': options, 'report_id': self.id, 'report_model': self._name})[0]
        return pdf_datas

    def action_print_report_pdf_detailed(self, options, **kwargs):
        context = dict(self._context.get('context'))
        context['is_pdf'] = True
        context['system_report'] = False
        self = self.with_context(context)
        filename = self.get_report_filename(options)
        return {
            'type': 'ir_actions_account_report_download',
            'data': {
                'report_name': filename,
                'output_format': 'pdf',
                'model': self._name,
                'report_id': self.id,
                'options': json.dumps(options),
                'context': json.dumps(context),
            },
        }

    def action_print_report_pdf_summary(self, options, **kwargs):
        context = dict(self._context.get('context'))
        context['summary_report'] = True
        self = self.with_context(context)
        filename = self.get_report_filename(options)
        return {
            'type': 'ir_actions_account_report_download',
            'data': {
                'report_name': filename,
                'output_format': 'pdf',
                'model': self._name,
                'report_id': self.id,
                'options': json.dumps(options),
                'context': json.dumps(context),
                'folded': True
            },
        }

    def action_print_report_xlsx_detailed(self, options, **kwargs):
        context = dict(self._context.get('context'))
        self = self.with_context(context)
        filename = self.get_report_filename(options)
        return {
            'type': 'ir_actions_account_report_download',
            'data': {
                'report_name': filename,
                'output_format': 'xlsx',
                'model': self._name,
                'report_id': self.id,
                'options': json.dumps(options),
                'context': json.dumps(context),
            },
        }

    def action_print_report_xlsx_summary(self, options, **kwargs):
        context = dict(self._context.get('context'))
        self = self.with_context(context)
        filename = self.get_report_filename(options)

        return {
            'type': 'ir_actions_account_report_download',
            'data': {
                'report_name': filename,
                'output_format': 'xlsx',
                'model': self._name,
                'report_id': self.id,
                'options': json.dumps(options),
                'context': json.dumps(context),
                'folded': True
            },
        }

    def action_print_report_send_mail(self, options, **kwargs):
        context = dict(self._context.get('context'))
        landscape = True if len(options.get('headers')) > 5 else False
        context.update({'landscape': landscape})
        self = self.with_context(context)
        template_id = self.env['ir.model.data']._xmlid_to_res_id('ics_account_reports.finance_report_email_template', raise_if_not_found=False)
        title = self.get_title()
        filename = '{}.pdf'.format(title)
        AttachmentObj = self.env['ir.attachment']
        attachment = AttachmentObj.search([('name', '=', filename)], limit=1)
        pdf_datas = self.get_pdf(options)

        attachment = AttachmentObj.create({
            'name': filename,
            'datas': base64.b64encode(pdf_datas),
            'store_fname': filename,
            'res_model': self._name,
            'res_id': self.env.user.id,
            'type': 'binary',
            'mimetype': 'application/pdf'
        })
        ctx = {
            'default_model': 'res.users',
            'default_res_id': self.env.user.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'custom_layout': "mail.mail_notification_light",
            'default_attachment_ids': attachment.ids,
            'subject': title,
            'model_description': _('Report'),
        }

        return {
            'name': 'Report Send by Email: %s' % (title),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def get_account_report_section_data(self, parent, options, **kwargs):
        return []

    def action_open_moves(self, account_id, options, **kwargs):
        action = self.env["ir.actions.act_window"]._for_xml_id("account.action_account_moves_all")
        action = clean_action(action, env=self.env)
        date_from, date_to = self._get_dates_range(options, **kwargs)
        domain = [('parent_state', '=', 'posted')]
        if options.get('analytic_account_ids', []):
            domain += [('analytic_account_id', 'in', options.get('analytic_account_ids'))]
        if date_from:
            domain = expression.AND([domain, [('date', '>=', date_from)]])
        if date_to:
            domain = expression.AND([domain, [('date', '<=', date_to)]])
        action['domain'] = [('account_id', '=', account_id)] + domain
        action['context'] = {'create': 0, 'delete': 0}
        return action

    def action_open_move(self, move_id, options, **kwargs):
        action = self.env["ir.actions.act_window"]._for_xml_id("account.action_move_journal_line")
        form_view = [(self.env.ref('account.view_move_form').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        action['res_id'] = move_id
        return action

    def get_report_filename(self, options):
        dates = options.get('date', {})
        date_to = dates.get('date_to', fields.Date().today())
        date_from = dates.get('date_from', fields.Date.start_of(fields.Date.from_string(date_to), 'year'))
        period = '_(' + date_from + ' to ' + date_to + ')'
        return self.get_title().lower().replace(' ', '_') + period

    # Excel file method starts
    def excel_get_worksheet_with_header(self, workbook, options):
        worksheet = workbook.add_worksheet()
        headers = options.get('headers')
        heading_style = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '16', 'valign': 'vcenter'})
        sub_heading_style = workbook.add_format({'align': 'left', 'bold': True, 'font_size': '11', 'valign': 'vcenter'})
        title_heading_style = workbook.add_format({'align': 'right', 'bold': True, 'font_size': '11', 'valign': 'vcenter'})

        dates = options.get('date', {})
        date_to = dates.get('date_to', fields.Date().today())
        date_from = dates.get('date_from', fields.Date.start_of(fields.Date.from_string(date_to), 'year'))
        if date_from:
            period = ' (' + format_date(self.env, date_from) + ' to ' + format_date(self.env, date_to) + ')'
        else:
            period = ' (to ' + format_date(self.env, date_to) + ')'

        header_row = 0
        worksheet.merge_range(0, 0, 1, len(headers), '')
        worksheet.write(header_row, 0, self.get_title() + period, heading_style)
        header_row += 2

        worksheet.merge_range(header_row, 0, header_row, len(headers), '')
        worksheet.write(header_row, 0, options['date']['string'], sub_heading_style)
        header_row += 1

        worksheet.merge_range(header_row, 0, header_row, len(headers), '')
        worksheet.write(header_row, 0, 'Company: {}'.format(options['company']), sub_heading_style)
        header_row += 1

        worksheet.merge_range(header_row, 0, header_row, len(headers), '')
        worksheet.write(header_row, 0,
                        'Period: {} to {}'.format(format_date(self.env, options['date']['date_from']) or '',
                                                  format_date(self.env, options['date']['date_to'])), sub_heading_style)
        header_row += 1

        if options.get('filters'):
            for dummy, filter_data in options.get('filters').items():
                if filter_data.get('res_ids'):
                    data_id = self.env[filter_data.get('res_model')].browse(filter_data.get('res_ids'))
                    worksheet.write(header_row, 0, filter_data.get('string'), sub_heading_style)
                    worksheet.merge_range(header_row, 1, header_row, len(data_id) + 2, '')
                    worksheet.write(header_row, 1, ', '.join(data_id.mapped('display_name')))
                    header_row += 1
        if options.get('downloaded_by', False) and options.get('downloaded_at', False):
            worksheet.write(header_row, 0, "Printed By", sub_heading_style)
            worksheet.write(header_row, 1, options.get('downloaded_by'))
            worksheet.write(header_row, 2, options.get('downloaded_at'))
            header_row += 1
        else:
            worksheet.write(header_row, 0, "Printed By", sub_heading_style)
            worksheet.write(header_row, 1, self.env.user.name)
            timezone = self._context.get('tz') or self.env.user.partner_id.tz or 'UTC'
            worksheet.write(header_row, 2, format_datetime(self.env, fields.Datetime.now(), tz=timezone, dt_format=False))
            header_row += 1
        header_row += 1

        for col, header in enumerate(headers):
            worksheet.write(header_row, col + 1, header, title_heading_style)

        # Set column width
        if self._name == 'account.finance.report':
            [worksheet.set_column(1, col, 50) for col in range(0, len(headers) + 1)]
        else:
            [worksheet.set_column(1, col, 20) for col in range(0, len(headers) + 1)]
        return worksheet, header_row + 1

    def excel_add_section_children(self, workbook, worksheet, options, row, line):
        cell_right = workbook.add_format({'align': 'right', 'valign': 'vcenter'})
        for detail_line in line['children']:
            indent = ' ' * 4 * detail_line['level']
            indent_style = workbook.add_format({'align': 'left', 'valign': 'vcenter'})
            worksheet.write(row, 0, indent + detail_line['title'], indent_style)
            column = 1
            for line_key in detail_line['values']:
                vals = ''
                if detail_line['values'][line_key]:
                    vals = detail_line['values'][line_key][0]
                    vals = tuple(vals)[1] if isinstance(vals, tuple) else vals
                worksheet.write(row, column, vals, cell_right)
                column += 1
            row += 1
            if detail_line['children']:
                row = self.excel_add_section_children(workbook, worksheet, options, row, detail_line)
            elif not options.get('folded'):
                if detail_line['group_by']:
                    for lines in self.get_account_report_section_data(detail_line, options):
                        if lines:
                            balance = 0.0
                            row, balance = self.excel_add_section_line(workbook, worksheet, row, lines, balance)
        return row

    def excel_add_section_line(self, workbook, worksheet, row, detail_line, balance):
        indent = ' ' * 4 * detail_line['level']
        indent_style = workbook.add_format({'align': 'left', 'valign': 'vcenter'})
        cell_right = workbook.add_format({'align': 'right', 'valign': 'vcenter'})
        worksheet.write(row, 0, indent + detail_line['title'], indent_style)
        column = 1
        if balance in [0.0, '']:
            balance = detail_line.get('balance', 0)
        for line_key in detail_line['values']:
            vals = ''
            if line_key == 'Balance':
                if detail_line['values'][line_key]:
                    vals = detail_line['values'][line_key][0]
            else:
                if detail_line['values'][line_key]:
                    vals = detail_line['values'][line_key]
                    vals = tuple(vals)[0] if isinstance(vals, tuple) else vals
            worksheet.write(row, column, vals, cell_right)
            column += 1
        row += 1
        return row, balance

    def excel_write_report_lines(self, workbook, worksheet, options, row):
        bold_right_text = workbook.add_format({'align': 'right', 'valign': 'vcenter', 'bold': True})
        bold_left_text = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'bold': True})
        total_left_text = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'bold': True, 'top': 2})
        total_right_text = workbook.add_format({'align': 'right', 'valign': 'vcenter', 'bold': True})
        section_text = workbook.add_format({'align': 'right', 'valign': 'vcenter', 'bold': True, 'bottom': 6})
        section_left_text = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'bold': True, 'bottom': 6})
        sections = self._get_sections(self.section_ids, options, {}) if self._name == 'account.finance.report' else self._get_sections(options)
        for line in sections:
            title = str(line.get('title', ''))
            if line.get('level') == 0:
                style = section_left_text
            elif line.get('id') == 'total':
                style = total_left_text
            else:
                style = bold_left_text
            worksheet.write(row, 0, title, style)

            opening_balance = 'Opening Balance' in line.get('values') and line.get('values')['Opening Balance'][0] or 0
            # Do not add Opening Balance Column for other reports (Where Opening balance not found in values)
            if 'Opening Balance' in line.get('values'):
                worksheet.write(row, 6, opening_balance, total_right_text)

            column = 1
            for line_key in line['values']:
                if line.get('level') == 0:
                    style = section_text
                elif line.get('id') == 'total':
                    style = total_right_text
                else:
                    style = bold_right_text
                vals = ''
                if line['values'][line_key]:
                    vals = line['values'][line_key][0]
                    vals = tuple(vals)[1] if isinstance(vals, tuple) else vals
                worksheet.write(row, column, vals, style)
                column += 1
            row += 1
            if self._name == 'account.finance.report' and line['children']:
                row = self.excel_add_section_children(workbook, worksheet, options, row, line)
            if self._name != 'account.finance.report' and line['id'] != 'total' and not options.get('folded'):
                balance = 0.0
                for detail_line in self.get_account_report_section_data(line, options):
                    row, balance = self.excel_add_section_line(workbook, worksheet, row, detail_line, balance)
        return worksheet, row

    # Excel file method ends
    def get_excel(self, options):
        # Create an in-memory Excel file
        output = io.BytesIO()

        # Write the data
        workbook = xlsxwriter.Workbook(output)
        worksheet, row = self.excel_get_worksheet_with_header(workbook, options)
        worksheet, row = self.excel_write_report_lines(workbook, worksheet, options, row)

        # Close the workbook
        workbook.close()
        return output.getvalue()
