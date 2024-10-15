
from dateutil.relativedelta import relativedelta
from odoo import models, fields, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from itertools import chain


class PartnerAgedReportHandler(models.AbstractModel):
    _name = 'partner.aged.report.handler'
    _inherit = 'mixin.report.handler'
    _description = 'Partner Aged Report Handler'
    _override_sections_data = True
    _override_section_detail = True

    def _get_report_filename(self, report, options, **kwargs):
        return _('Aged Receivable Report') if self.env.context.get('report_type') == 'receivable' else _('Aged Payable Report')

    def _get_report_title(self, report):
        return _('Aged Receivable Report') if self.env.context.get('report_type') == 'receivable' else _('Aged Payable Report')

    def _get_total_label(self):
        return _('Aged Receivable') if self.env.context.get('report_type') == 'receivable' else _('Aged Payable')

    def _get_handler_domain(self, report, options, **kwargs):
        payable_domain = []
        non_trade_payable_domain = []
        filter_accounts = options.get('dynamic_filter_search', {}).get('filter_account', [])
        for filter_key in filter_accounts:
            if filter_key == 'payable':
                payable_domain = [('account_id.internal_type', '=', self.env.context.get('report_type')), ('account_id.non_trade_payable', '=', False)]
            elif filter_key == 'non_trade_payable':
                non_trade_payable_domain = [('account_id.internal_type', '=', self.env.context.get('report_type')), ('account_id.non_trade_payable', '=', True)]

        domain = expression.OR([payable_domain, non_trade_payable_domain]) if non_trade_payable_domain else payable_domain
        if not domain:
            domain = [('account_id.non_trade_payable', '=', False), ('account_id.internal_type', '=', self.env.context.get('report_type'))]
        return super()._get_handler_domain(report, options, **kwargs) + domain

    def _get_column_label(self, column, options, **kwargs):
        period_days = self.get_period_user_input_days(options)
        if column.expression_label == 'invoice_date':
            return _('Invoice Date') if self.env.context.get('report_type') == 'receivable' else _('Bill Date')
        if column.expression_label == 'period0':
            return options.get('filter_date_options').get('string')
        if column.expression_label.startswith('period') and column.expression_label != 'period0':
            period_count = int(column.expression_label.replace('period', ''))
            to_range = period_count * period_days if period_count < 5 else (period_count - 1) * period_days
            from_range = (to_range - period_days) + 1
            return '{} - {}'.format(from_range, to_range) if period_count < 5 else '> {}'.format(to_range)
        return super()._get_column_label(column, options, **kwargs)

    def _get_filter_label(self, report_filter, options, **kwargs):
        name = super()._get_filter_label(report_filter, options, **kwargs)
        if report_filter.filter_key == 'filter_account':
            choice_ids = report_filter.choice_ids
            option_value = options.get('dynamic_filter_search', {}).get(report_filter.filter_key)
            default_choice = choice_ids.filtered(lambda choice: option_value and (choice.choice_key == option_value or choice.choice_key in option_value))
            if not default_choice:
                default_choice = choice_ids.filtered(lambda choice: choice.is_default)
            if sorted(choice_ids.mapped('choice_key')) == sorted(option_value or []):
                choice_names = _('All')
            else:
                choice_names = ','.join([self._get_choice_label(choice) for choice in default_choice])
            return '{} {}'.format(report_filter.name, choice_names)
        if report_filter.filter_key == 'filter_based_on':
            choice_ids = report_filter.choice_ids
            option_value = options.get('dynamic_filter_search', {}).get(report_filter.filter_key)
            default_choice = choice_ids.filtered(lambda choice: option_value and (choice.choice_key == option_value))
            if not default_choice:
                default_choice = choice_ids.filtered(lambda choice: choice.is_default)
            return "{} {}".format(report_filter.name, default_choice and self._get_choice_label(default_choice[0]) or '')
        return name

    def _get_choice_label(self, choice):
        if choice.choice_key == 'payable':
            return _('Receivable') if self.env.context.get('report_type') == 'receivable' else _('Payable')
        if choice.choice_key == 'non_trade_payable':
            return _('Non Trade Receivable') if self.env.context.get('report_type') == 'receivable' else _('Non Trade Payable')
        if choice.choice_key == 'date':
            return _('Invoice Date') if self.env.context.get('report_type') == 'receivable' else _('Bill Date')
        return choice.name

    def _get_filter_options(self, filter, options, **kwargs):
        options = super()._get_filter_options(filter, options, **kwargs)
        if filter.ir_model_field_id.name == 'partner_id':
            # FIXME: freight_base dependency is not there, move this method under fm_operation_reports or create category inside ics_account
            category_ids = self.env.ref('freight_base.org_type_customer' if self.env.context.get('report_type') == 'receivable' else 'freight_base.org_type_vendor').ids
            partner_domain = ['|', ('category_ids', 'in', category_ids), ('category_ids', '=', False)]
            options.update({
                'string': _('Customer') if self.env.context.get('report_type') == 'receivable' else _('Vendor'),
                'domain': partner_domain
            })
        if filter.filter_key in ['filter_account', 'filter_based_on']:

            options.update({
                'choices': [{
                    'label': self._get_choice_label(choice),
                    'choice_key': choice.choice_key,
                    'choice_id': '{}_{}_{}'.format(filter.filter_key, choice.choice_key, choice.id),
                    'is_default': choice.is_default,
                } for choice in filter.choice_ids]
            })
        return options

    def _report_handler_partner_aged_values(self, report, report_line, data_fields, options, current_group_by, **kwargs):
        period_days = self.get_period_user_input_days(options)
        based_on_date = 'date_maturity' if options.get('dynamic_filter_search', {}).get('filter_based_on') == 'due_date' else 'invoice_date'
        date_to = options.get('filter_date_options').get('date_to')
        period_domains = self._get_period_domain_vals(date_to, period_days=period_days)
        domain = report._get_default_domain(options, ignore_date_domain=not report_line.strict_on_date_range, **kwargs)

        if kwargs.get('__filter_domain'):
            domain += kwargs.get('__filter_domain', [])

        data_fields = report_line.expression_ids.filtered(lambda exp: exp.computation_engine == 'field').mapped('name')
        records = self._get_period_query_result(report, domain, options, period_domains, date_to, current_group_by=current_group_by, fields=data_fields, based_on_date=based_on_date, **kwargs)

        section_records = []
        group_total_row = []

        group_title = self._get_total_label()

        if not kwargs.get('group_total') and current_group_by == 'id':
            for record in records:
                line_record = self.env[report.model_name].with_context(prefetch_fields=False).browse(record.get('move_line_ids'))
                group_title = line_record.partner_id.display_name
                section_records.append({
                    **record,
                    'id': line_record.id,
                    'name': line_record.move_name,
                    'label': line_record.get_report_label_name(),
                    'account_id': line_record.account_id.code,
                    'currency_code': line_record.currency_id.name,
                    'amount_residual': sum([record.get(f'period{i}', 0) for i in range(len(period_domains))])
                })
        else:

            # Grouping by Partners
            distinct_partner_ids = list(set(map(lambda rec: rec['partner_id'], records)))
            for partner_id in distinct_partner_ids:
                partner_records = list(filter(lambda x: x.get('partner_id') == partner_id, records))

                amount_residual = 0
                period_result = {}

                for i in range(len(period_domains)):
                    period_key = f'period{i}'
                    period_result[period_key] = sum(list(map(lambda rec: rec[period_key], partner_records)))
                    amount_residual += period_result[period_key]

                section_records.append({
                    'label': '',
                    'date': '',
                    'date_maturity': '',
                    'account_id': '',
                    'currency_id': '',
                    'currency_code': '',
                    'partner_id': partner_id,
                    **period_result,
                    'amount_currency': 0,
                    'amount_residual': amount_residual
                })

        # Formating records in section
        sections = report_line._groups_to_sections(section_records, current_group_by, options, **kwargs)
        if not kwargs.get('group_total') and current_group_by == 'partner_id':
            sections = sorted(sections, key=lambda x: (self.env['res.partner'].browse(x['id']).mapped('name')[0].lower(), x['id']))

        # If group total row found
        if section_records:

            period_result = {}
            amount_residual = 0

            for i in range(len(period_domains)):
                period_key = f'period{i}'
                period_result[period_key] = sum(list(map(lambda rec: rec[period_key], section_records)))
                amount_residual += period_result[period_key]

            group_total_row.append({
                'label': '',
                'date': '',
                'date_maturity': '',
                'account_id': '',
                'currency_id': '',
                'currency_code': '',
                'partner_id': section_records[0].get('partner_id'),
                **period_result,
                'amount_currency': 0,
                'amount_residual': amount_residual
            })

            kwargs['sub_group_by'] = None
            kwargs['group_total'] = True
            kwargs['level'] = 2

            sections += report_line._groups_to_sections(group_total_row, current_group_by, options, extra_params={
                'action': False,
                'foldable': False,
                'group_total': True,
                'title': _('Total {}'.format(group_title))
            }, **kwargs)

        return sections

    def _get_period_query_result(self, report, domain, options, periods, max_date, current_group_by, fields=[], based_on_date='date_maturity', **kwargs):

        tables, where_clause, where_params = report._generate_query_params(options, domain=domain, fields=fields, **kwargs)

        age_period_table = ('(VALUES %s) AS age_period_table (period_index, date_start, date_stop)' % ','.join("(%s, %s, %s)" for i, period in enumerate(periods)))
        params = list(chain.from_iterable((i, periods.get(period)[0] or None, periods.get(period)[1] or None) for i, period in enumerate(periods)))
        age_period_table_query = self.env.cr.mogrify(age_period_table, params).decode(self.env.cr.connection.encoding)

        period_query = ','.join([f"""
            CASE WHEN age_period_table.period_index = {i}
                THEN SUM(account_move_line.balance) - COALESCE(SUM(part_debit.amount), 0) + COALESCE(SUM(part_credit.amount), 0)
            ELSE 0 END AS period{i}
        """ for i in range(len(periods))])

        select_fields = ','.join([f'account_move_line.{field_name}' for field_name in fields])
        group_by_fields = f'account_move_line.{current_group_by}, age_period_table.period_index, {select_fields}'

        query = f"""
                SELECT
                    {select_fields},
                    ARRAY_AGG(DISTINCT account_move_line.id) as move_line_ids,
                    account_move_line.partner_id as partner_id,
                    (
                        SUM(account_move_line.amount_currency) - COALESCE(SUM(part_debit.debit_amount_currency), 0) + COALESCE(SUM(part_credit.credit_amount_currency), 0)
                    ) AS amount_currency,
                    {period_query}
                FROM {tables}
                JOIN account_account as account ON account.id = account_move_line.account_id
                    LEFT JOIN LATERAL (
                    SELECT
                        SUM(part.amount) AS amount,
                        SUM(part.debit_amount_currency) AS debit_amount_currency,
                        part.debit_move_id
                    FROM account_partial_reconcile part
                    WHERE part.max_date <= %s
                    GROUP BY part.debit_move_id
                ) part_debit ON part_debit.debit_move_id = account_move_line.id
                LEFT JOIN LATERAL (
                    SELECT
                        SUM(part.amount) AS amount,
                        SUM(part.credit_amount_currency) AS credit_amount_currency,
                        part.credit_move_id
                    FROM account_partial_reconcile part
                    WHERE part.max_date <= %s
                    GROUP BY part.credit_move_id
                ) part_credit ON part_credit.credit_move_id = account_move_line.id
                JOIN {age_period_table_query} ON
                    (
                        age_period_table.date_start is NULL
                        OR COALESCE(account_move_line.{based_on_date}, account_move_line.date) <= DATE(age_period_table.date_start)
                    )
                    AND
                    (
                        age_period_table.date_stop is NULL
                        OR COALESCE(account_move_line.{based_on_date}, account_move_line.date) >= DATE(age_period_table.date_stop)
                    )
                WHERE {where_clause}
                GROUP BY {group_by_fields}
                HAVING
                (SUM(ROUND(account_move_line.debit, 3)) - COALESCE(SUM(ROUND(part_debit.amount, 3)), 0)) != 0
                OR
                (SUM(ROUND(account_move_line.credit, 3)) - COALESCE(SUM(ROUND(part_credit.amount, 3)), 0)) != 0
        """

        max_date = max_date.strftime(DEFAULT_SERVER_DATE_FORMAT) if max_date and not isinstance(max_date, str) else max_date

        params = [max_date, max_date, *where_params]
        self._cr.execute(query, params)
        return self._cr.dictfetchall()

    def _get_period_domain_vals(self, date_to, period_days=30):

        def get_domain(date_obj, from_day, to_day):
            from_date = None
            to_date = None
            today = fields.Date.today()

            if date_obj > today:
                date_obj = today

            if from_day is not False:
                from_date = fields.Date.to_string(date_obj - relativedelta(days=from_day))

            if to_day is not False:
                to_date = fields.Date.to_string(date_obj - relativedelta(days=to_day))

            return from_date, to_date

        date_to = fields.Date.from_string(date_to)
        period_values = {
            'period0': get_domain(date_to, False, 0),
            'period1': get_domain(date_to, 1, period_days),
            'period2': get_domain(date_to, (period_days * 1) + 1, period_days*2),
            'period3': get_domain(date_to, (period_days * 2) + 1, period_days*3),
            'period4': get_domain(date_to, (period_days * 3) + 1, period_days*4),
            'period5': get_domain(date_to, (period_days * 4) + 1, False),
        }
        return period_values

    def _get_section_detail_data(self, report, section_line, options, parent, **kwargs):
        super()._get_section_detail_data(report, section_line, options, parent, **kwargs)

        group_by_fields = list(set(section_line.group_by_fields.split(',')) - set([parent.get('code')]))
        group_by = group_by_fields[0]

        filter_domain = [('partner_id', '=', parent.get('id'))]

        return self._report_handler_partner_aged_values(report, section_line, [], options, group_by, __filter_domain=filter_domain, **kwargs)

    def get_period_user_input_days(self, options):
        period_days = 30
        if options.get('filter_dynamic_filters'):
            period_days_lst = [filter['default_value'] for filter in options['filter_dynamic_filters'] if filter['filter_key'] == 'filter_day_range' and filter['filter_type'] == 'input']
            return int(float(period_days_lst[0])) if period_days_lst else 30
        return period_days
