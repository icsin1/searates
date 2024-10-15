from odoo import models, _


class AccountGeneralLedgerHandler(models.AbstractModel):
    _name = 'account.general.ledger.handler'
    _inherit = 'mixin.report.handler'
    _description = 'Account General Ledger Handler'
    _override_sections_data = True
    _override_section_detail = True

    def _get_report_filename(self, report, options, **kwargs):
        return _('General Ledger')

    def _get_report_title(self, report):
        return _('General Ledger')

    def _get_section_detail_data(self, report, report_line, options, parent, **kwargs):
        sections = super()._get_section_detail_data(report, report_line, options, parent, **kwargs)

        group_by_fields = list(set(report_line.group_by_fields.split(',')) - set([parent.get('code')]))
        group_by = group_by_fields[0]

        data_fields = report_line.expression_ids.filtered(lambda exp: exp.computation_engine == 'field').mapped('name')

        sections += self._get_section_detail_general_ledger_values(report, report_line, parent, data_fields, options, group_by=group_by, **kwargs)
        return sections

    def _get_section_detail_general_ledger_values(self, report, report_line, parent_section, fields, options, group_by, **kwargs):
        filter_domain = [('account_id', '=', parent_section.get('id'))]
        filter_domain += report._get_default_domain(options, **kwargs)
        fields += ['partner_id', 'account_id', 'amount_currency']
        records = self._get_query_result(report, report_line, fields, options, domain=filter_domain, current_group_by=group_by, **kwargs)

        aggregate_fields = report_line.expression_ids.filtered(lambda exp: exp.allow_aggregate and exp.computation_engine == 'field').mapped('name')

        section_records = []
        account_ids = [rec.get('account_id') for rec in records if rec.get('account_id')]
        accounts = {account.id: account for account in self.env['account.account'].browse(account_ids)}

        currency_ids = [rec.get('currency_id') for rec in records if rec.get('currency_id')]
        currencies = {account.id: account for account in self.env['res.currency'].browse(currency_ids)}

        partner_ids = [rec.get('partner_id') for rec in records if rec.get('partner_id')]
        partners = {account.id: account for account in self.env['res.partner'].browse(partner_ids)}

        parent_initial_balance = parent_section.get('values', {}).get('main_group', {}).get('initial_balance_original', 0)

        for idx, record in enumerate(records):
            account = accounts.get(record.get('account_id', 0))
            currency = currencies.get(record.get("currency_id", 0))
            partner = partners.get(record.get('partner_id'), 0)
            aggregated_result = {field: record.get(field) for field in aggregate_fields}
            closing_balance = aggregated_result.get('debit') - aggregated_result.get('credit')
            aggregated_result.update({
                'initial_debit_balance': 0,
                'initial_credit_balance': 0,
                'closing_debit_balance': 0,
                'closing_credit_balance': 0
            })

            if idx > 0:
                previous_section = section_records[idx-1]
                closing_balance += previous_section.get("closing_balance")
            else:
                closing_balance += parent_initial_balance

            section_records.append({
                **record,
                'name': record.get('move_name'),
                'label': record.get('label', ''),
                'ref': record.get('ref', ''),
                'date': record.get('date'),
                'partner_id': partner and partner.name or '',
                'amount_foreign_currency': record.get("amount_currency", 0),
                'currency_id': currency and currency.name or '',
                'account_id': account and account.display_name or '',
                'initial_balance': '',
                'closing_balance': closing_balance,
                **aggregated_result
            })

        return report_line._groups_to_sections(section_records, 'id', options, **kwargs)

    def _report_handler_general_ledger_values(self, report, report_line, data_fields, options, current_group_by, **kwargs):
        """ Need to generate below values for each group of records
            label, ref, partner_id, amount_foreign_currency, currency_id, initial_balance, closing_balance
        """
        domain = []
        if kwargs.get('__filter_domain'):
            domain += kwargs.get('__filter_domain', [])

        data_fields = report_line.expression_ids.filtered(lambda exp: exp.computation_engine == 'field').mapped('name')

        section_records, group_records = self._get_gl_records(report, report_line, data_fields, options, domain=domain, current_group_by=current_group_by, **kwargs)
        group_total_row = []

        # If group total row found
        if section_records:

            aggregated_result = self._compute_aggregated_values(report, report_line, group_records, [], options, only_fields=False, **kwargs)

            group_total_row.append({
                'label': '',
                'ref': '',
                'date': '',
                'amount_foreign_currency': '',
                'currency_id': '',
                'account_id': group_records[0].get('account_id'),
                'initial_balance': 0,
                'closing_balance': 0,
                **aggregated_result
            })

            kwargs['sub_group_by'] = None
            kwargs['group_total'] = True
            kwargs['level'] = 2

            section_records += report_line._groups_to_sections(group_total_row, current_group_by, options, extra_params={
                'action': False,
                'foldable': False,
                'group_total': True,
                'title': _('Total')
            }, **kwargs)

        return section_records

    def _get_gl_records(self, report, report_line, fields, options, domain=[], **kwargs):
        section_records = []
        current_group_by = kwargs.get('current_group_by')
        # Getting all accounts other then unaffected earnings and income/expense accounts
        account_records = self._get_gl_account_records(report, report_line, fields, options, domain=domain, **kwargs)
        section_records += report_line._groups_to_sections(account_records, current_group_by, options, **kwargs)

        # Getting all accounts related to income / expense
        earning_records = self._get_gl_earning_records(report, report_line, fields, options, domain=domain, **kwargs)
        section_records += report_line._groups_to_sections(earning_records, current_group_by, options, **kwargs)

        # Getting all unaffected earning related data
        unaffected_records = self._get_gl_unaffected_earning_records(report, report_line, fields, options, domain=domain, **kwargs)
        kwargs.update({'sub_group_by': 'id'})
        extra_params = {'row_class': 'font-weight-bold font-italic'}
        section_records += report_line._groups_to_sections(unaffected_records, current_group_by, options, extra_params=extra_params, **kwargs)

        return section_records, (account_records + earning_records + unaffected_records)

    def _get_gl_account_records(self, report, report_line, fields, options, current_group_by, domain=[], **kwargs):
        """ Getting all the account initial balance and selected period data with given filter and options.
        """
        filter_domain = [
            ('account_id.user_type_id', '!=', self.env.ref('account.data_unaffected_earnings').id),
            ("account_id.user_type_id.internal_group", "not in", ["income", "expense"])
        ]
        account_domain = domain + filter_domain
        account_domain += report._get_default_domain(options, **kwargs)
        records = self._get_query_result(report, report_line, fields, options, domain=account_domain, current_group_by=current_group_by, **kwargs)

        date_options = options.get('filter_date_options')

        section_records = []

        # Getting opening balance for all including current period accounts
        previous_period_domain = filter_domain + report_line.expression_ids[0]._get_date_range_domain(
            date_options,
            date_scope='from_begin_period'
        )

        previous_period_records = self._get_query_result(
            report, report_line, fields, options, domain=previous_period_domain, current_group_by=current_group_by, ignore_date_domain=True, **kwargs
        )

        section_records += self._generate_section_data(report, report_line, records, previous_period_records, current_group_by, options, **kwargs)

        return section_records

    def _get_gl_earning_records(self, report, report_line, fields, options, current_group_by, domain=[], **kwargs):
        filter_domain = [("account_id.user_type_id.internal_group", "in", ["income", "expense"])]
        earning_domain = domain + filter_domain
        earning_domain += report._get_default_domain(options, **kwargs)
        records = self._get_query_result(report, report_line, fields, options, domain=earning_domain, current_group_by=current_group_by, **kwargs)

        section_records = []
        date_options = options.get('filter_date_options')

        # Getting opening balance as on fiscal year start to previous period end
        previous_period_domain = filter_domain + report_line.expression_ids[0]._get_date_range_domain(date_options, date_scope='from_begin_period')
        f_date_from, _ = report._get_date_value_for_range(date_options.get('date_to'), 'today', 'this_year', {})
        previous_period_domain += [(report.date_field.name, '>=', f_date_from)]

        previous_period_records = self._get_query_result(
            report, report_line, fields, options, domain=previous_period_domain, current_group_by=current_group_by, ignore_date_domain=True, **kwargs
        )

        section_records += self._generate_section_data(report, report_line, records, previous_period_records, current_group_by, options, **kwargs)

        return section_records

    def _get_gl_unaffected_earning_records(self, report, report_line, fields, options, current_group_by, domain=[], **kwargs):

        unaffected_earning_account = self.env['account.account'].search([('user_type_id', '=', self.env.ref('account.data_unaffected_earnings').id)], limit=1)
        unaffected_earning_domain = domain + [('account_id.user_type_id', '=', self.env.ref('account.data_unaffected_earnings').id)]
        unaffected_earning_domain += report._get_default_domain(options, **kwargs)

        # Including period for current from fiscal year to selected date end
        date_options = options.get('filter_date_options')

        # Getting record for period of Fiscal year start to selected end date
        group_records = self._get_query_result(report, report_line, fields, options, domain=unaffected_earning_domain, ignore_date_domain=True, current_group_by=current_group_by, **kwargs)

        section_records = []

        date_options = options.get('filter_date_options')

        # Getting previous fiscal year earning for undistributed profit/loss
        previous_year_earning = [("account_id.user_type_id.internal_group", "in", ["income", "expense"])]

        previous_year_earning += report_line.expression_ids[0]._get_date_range_domain(
            date_options,
            date_scope='from_begin_fiscal_year'
        )
        previous_year_earning_records = self._get_query_result(report, report_line, fields, options, domain=previous_year_earning, current_group_by=current_group_by, ignore_date_domain=True, **kwargs)

        # Getting all undistributed entries till last period end date
        opening_undistributed_domain = [('account_id.user_type_id', '=', self.env.ref('account.data_unaffected_earnings').id)]
        opening_undistributed_domain += report_line.expression_ids[0]._get_date_range_domain(
            date_options,
            date_scope='from_begin_period'
        )
        previous_unallocated_records = self._get_query_result(report, report_line, fields, options, domain=opening_undistributed_domain, current_group_by=current_group_by, ignore_date_domain=True,
                                                              **kwargs)

        # Clubbing last fiscal year earnings with unallocated entries from opening to last period end date
        previous_year_records = previous_year_earning_records + previous_unallocated_records

        # nothing found returning empty list
        if not (group_records + previous_year_records):
            return []

        aggregated_result = self._compute_aggregated_values(report, report_line, group_records, previous_year_records, options, **kwargs)

        section_records.append({
            'label': '',
            'ref': '',
            'date': '',
            'amount_foreign_currency': '',
            'currency_id': '',
            'account_id': unaffected_earning_account.id,
            **aggregated_result
        })

        return section_records

    def _generate_section_data(self, report, report_line, records, previous_records, current_group_by, options, **kwargs):
        section_records = []
        if not (records + previous_records):
            return []
        # Grouping by accounts for current period record + initial records
        distinct_account_ids = list(set(map(lambda rec: rec[current_group_by], records + previous_records)))
        for account_id in distinct_account_ids:
            group_records = list(filter(lambda x: x.get(current_group_by) == account_id, records))
            previous_groups_records = list(filter(lambda x: x.get(current_group_by) == account_id, previous_records))

            aggregated_result = self._compute_aggregated_values(report, report_line, group_records, previous_groups_records, options, **kwargs)

            section_records.append({
                'label': '',
                'ref': '',
                'date': '',
                'amount_foreign_currency': '',
                'currency_id': '',
                'account_id': account_id,
                **aggregated_result
            })
        return section_records

    def _compute_aggregated_values(self, report, report_line, records, previous_records, options, only_fields=True, **kwargs):
        aggregate_expressions = report_line.expression_ids.filtered(lambda exp: exp.allow_aggregate)
        if only_fields:
            aggregate_expressions = aggregate_expressions.filtered(lambda exp: exp.computation_engine == 'field')
        aggregate_fields = aggregate_expressions.mapped('name')

        aggregated_result = {field: 0 for field in aggregate_fields}
        for aggregated_field in aggregated_result.keys():
            aggregated_result[aggregated_field] = sum(list(map(lambda rec: rec.get(aggregated_field), records)))

        # Creating balance from previous year data
        previous_aggregated = {field: 0 for field in aggregate_fields}
        for agg_field in previous_aggregated.keys():
            previous_aggregated[agg_field] = sum(list(map(lambda rec: rec[agg_field], previous_records)))

        # only fields will not compute init and closing so forcing to compute
        if only_fields:
            initial_balance = previous_aggregated.get('debit') - previous_aggregated.get('credit')
            closing_balance = initial_balance + aggregated_result.get('debit') - aggregated_result.get('credit')

            initial_impact_balance = sum(list(map(lambda rec: rec.get('debit', 0), previous_records))) - sum(list(map(lambda rec: rec.get('credit', 0), previous_records)))
            closing_impact_balance = initial_impact_balance + aggregated_result.get('debit', 0) - aggregated_result.get('credit', 0)

            aggregated_result.update({
                'initial_balance': initial_balance,
                'closing_balance': closing_balance,
                'initial_debit_balance': abs(initial_impact_balance) if initial_impact_balance > 0 else 0,
                'initial_credit_balance': abs(initial_impact_balance) if initial_impact_balance < 0 else 0,
                'closing_debit_balance': abs(closing_impact_balance) if closing_impact_balance > 0 else 0,
                'closing_credit_balance': abs(closing_impact_balance) if closing_impact_balance < 0 else 0,
            })
        else:
            initial_debit_balance = sum(list(map(lambda rec: rec.get('initial_debit_balance', 0), records + previous_records)))
            initial_credit_balance = sum(list(map(lambda rec: rec.get('initial_credit_balance', 0), records + previous_records)))

            closing_debit_balance = sum(list(map(lambda rec: rec.get('closing_debit_balance', 0), records + previous_records)))
            closing_credit_balance = sum(list(map(lambda rec: rec.get('closing_credit_balance', 0), records + previous_records)))
            aggregated_result.update({
                'initial_debit_balance': initial_debit_balance,
                'initial_credit_balance': initial_credit_balance,
                'closing_debit_balance': closing_debit_balance,
                'closing_credit_balance': closing_credit_balance,
            })
        return aggregated_result

    def _get_query_result(self, report, report_line, fields, options, domain=[], current_group_by=None, ignore_date_domain=False, **kwargs):
        tables, where_clause, where_params = report._generate_query_params(options, ignore_date_domain=ignore_date_domain, domain=domain, fields=fields, **kwargs)

        aggregate_fields = report_line.expression_ids.filtered(lambda exp: exp.allow_aggregate and exp.computation_engine == 'field').mapped('name')

        agg_select_fields = ','.join([f'SUM(account_move_line.{field_name}) AS {field_name}' for field_name in aggregate_fields])
        select_fields = ','.join([f'account_move_line.{field_name}' for field_name in fields if field_name not in aggregate_fields])
        agg_group_by_fields = ','.join([f'account_move_line.{field_name}' for field_name in aggregate_fields])

        group_by_fields = f'account_move_line.{current_group_by}, {select_fields}'

        query = f"""
            SELECT account_move_line.{current_group_by} as id, account_move_line.{current_group_by}, {agg_select_fields}, {select_fields}
            FROM {tables}
            WHERE {where_clause}
            GROUP BY {group_by_fields}, {select_fields}, {agg_group_by_fields}
        """
        self._cr.execute(query, where_params)
        return self._cr.dictfetchall()
