import re
from odoo import models, fields, _
from odoo.tools import format_date


class OutstandingStatementReport(models.Model):
    _name = 'outstanding.statement.report'
    _inherit = 'account.finance.report.mixin'
    _description = 'Outstanding Statement Report'

    def _is_customer_report(self):
        partner_type = self.env.context.get('partner_type')
        return partner_type == 'customer'

    def _get_buttons(self, options, **kwargs):
        """
        Override for add summary and details report in dropdown
        """
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

    def get_title(self):
        if self._is_customer_report():
            return _('Outstanding Customer Statement Report')
        return _('Outstanding Vendor Statement Report')

    def get_account_report_data(self, options, **kwargs):
        values = super().get_account_report_data(options, **kwargs)
        values['sections'] = self.get_sorted(options, self._get_sections(options, **kwargs))
        return values

    def _get_options(self, options, **kwargs):
        options = super()._get_options(options, **kwargs)
        options['sortable'] = True
        if not options.get('orderby') and not options.get('reverse'):
            options['orderby'] = 'Date'
            options['reverse'] = False
        if self._context.get('partner_type') == 'customer':
            domain = ['|', ('category_ids', 'in', self.env.ref('freight_base.org_type_customer').ids), ('category_ids', '=', False)]
        else:
            domain = ['|', ('category_ids', 'in', self.env.ref('freight_base.org_type_vendor').ids), ('category_ids', '=', False)]
        options['filters'] = {
            'partner_ids': {
                'string': _('Customer') if self._context.get('partner_type') == 'customer' else _('Vendor'),
                'res_model': 'res.partner',
                'res_field': 'partner_ids',
                'res_ids': options.get('partner_ids', []),
                'domain':  domain,
            }
        }
        return options

    def _get_column_headers(self, options, **kwargs):
        report_header = [
            _('Date'),
            _('Voucher Number'),
            _('Narration'),
            _('Due date'),
            _('Amount'),
            _('O/S Amount {}').format(self.env.company.currency_id.name),
            _('Running Total'),
            _('Aging'),
        ]
        context = self.env.context
        if context.get('summary_report'):
            report_header.insert(0, '')
        return report_header

    def _get_column_headers_properties(self, options, **kwargs):
        return {
            'Date': {'sortable': True},
            'Due date': {'sortable': True}
        }

    def _generate_domain(self, options, **kwargs):
        domain = super()._generate_domain(options, **kwargs)
        internal_type = 'payable' if not self._is_customer_report() else 'receivable'
        __, date_to = self._get_dates_range(options, **kwargs)
        domain = [
            ('date', '<=', date_to),
            ('account_id.internal_type', '=', internal_type),
            ('company_id', '=', self.env.company.id),
            ('parent_state', '=', 'posted'),
            '|', ('reconciled', '=', False),
            '|', ('matched_debit_ids.max_date', '>', date_to),
            ('matched_credit_ids.max_date', '>', date_to)
        ]
        ctx = self.env.context
        partner_type = ctx.get('partner_type')
        if partner_type == 'customer':
            domain += ['|', ('partner_id.category_ids', 'in', self.env.ref('freight_base.org_type_customer').ids), ('partner_id.category_ids', '=', False)]
        elif partner_type == 'vendor':
            domain += ['|', ('partner_id.category_ids', 'in', self.env.ref('freight_base.org_type_vendor').ids), ('partner_id.category_ids', '=', False)]
        if options.get('partner_ids'):
            domain += [('partner_id', 'in', options.get('partner_ids'))]
        else:
            domain += [('partner_id', '!=', False)]
        return domain

    def _get_sections(self, options, **kwargs):
        records = []
        MoveLineObj = self.env['account.move.line']
        data_domain = self._generate_domain(options, **kwargs)
        groups = self._get_account_values(data_domain, ['date', 'move_id', 'amount_residual', 'amount_currency'], ['partner_id'])
        context = self.env.context
        for record in groups:
            recs = MoveLineObj.search(record['__domain'])
            total_due_amount = self._compute_amount_total_currency_signed(options, recs)
            line_record = {
                'id': record.get('partner_id')[0],
                'title': record.get('partner_id')[1],
                'code': record.get('partner_id')[0],
                'level': 1,
                'group_by': 'partner_id',
                'values': {
                    'Date': '',
                    'Voucher Number': '',
                    'Narration': '',
                    'Due date': '',
                    'Amount': '',
                    'O/S Amount {}'.format(self.env.company.currency_id.name): (total_due_amount, self._format_currency(total_due_amount, currency=self.env.company.currency_id)),
                    'Running Total': (total_due_amount, self._format_currency(total_due_amount, currency=self.env.company.currency_id)),
                    'Ageing': '',
                }
            }
            if context.get('summary_report'):
                line_record.get('values').pop('Ageing')
            records.append(line_record)
        return self.get_sorted(options, records, True)

    def _compute_amount_total_currency_signed(self, options, move_line_ids):
        source_amount_currency = 0
        date_to = options.get('date').get('date_to')
        sign = 1
        for move_line in move_line_ids:
            part_debit = self.env['account.partial.reconcile'].search([('debit_move_id', '=', move_line.id), ('max_date', '<=', date_to)])
            part_credit = self.env['account.partial.reconcile'].search([('credit_move_id', '=', move_line.id), ('max_date', '<=', date_to)])
            amount_total_signed = sign * (sum(move_line.mapped('amount_currency')) - sum(part_debit.mapped('debit_amount_currency')) + sum(part_credit.mapped('credit_amount_currency')))
            move_id = move_line.move_id
            if move_id.currency_id.id == self.env.company.currency_id.id:
                source_amount_currency += amount_total_signed
            else:
                source_amount_currency += move_id.currency_id._convert(
                    amount_total_signed,
                    self.env.company.currency_id,
                    self.env.company,
                    fields.Date.today(),
                )
        return source_amount_currency

    def get_count_days(self, from_day, to_day):
        start_day = fields.Date.from_string(from_day)
        end_day = fields.Date.from_string(to_day)
        return (end_day - start_day).days

    def _html_to_text(self, html_value):
        # Removing <br> with \n
        html_value = str(html_value or '').replace("<br>", "\n")
        # and removing all HTML tags
        return re.sub(r'<[^<]+?>', '', html_value)

    def _get_order_by(self, options, **kwargs):
        order = 'DESC' if options.get('reverse') else 'ASC'

        line_order = {
            'Date': f'date {order}',
            'Due date': f'date_maturity {order}',
            'Amount': f'amount_residual_currency {order}',
            'Voucher Number': f'move_name {order}',
            'O/S Amount {}'.format(self.env.company.currency_id.name): 'amount_residual_currency',
        }

        record_order_by = 'date'
        if line_order.get(options.get('orderby')):
            record_order_by = line_order.get(options.get('orderby'))
        return record_order_by

    def get_account_report_section_data(self, parent, options, **kwargs):
        sign = 1
        date_to = options.get('date').get('date_to')
        line_data = []
        running_total = []
        partner_domain = [('partner_id', '=', parent.get('id'))]
        data_domain = partner_domain + self._generate_domain(options, **kwargs)
        data_domain + [('payment_id', '=', False)]

        move_line_ids = self.env['account.move.line'].sudo().search(data_domain, order=self._get_order_by(options, **kwargs))
        home_currency_code = self.env.company.currency_id.name
        for move_line in move_line_ids.sudo():
            move = move_line.move_id
            part_debit = self.env['account.partial.reconcile'].search([('debit_move_id', '=', move_line.id), ('max_date', '<=', date_to)])
            part_credit = self.env['account.partial.reconcile'].search([('credit_move_id', '=', move_line.id), ('max_date', '<=', date_to)])
            total = sign * (sum(move_line.mapped('amount_currency')) - sum(part_debit.mapped('debit_amount_currency')) + sum(part_credit.mapped('credit_amount_currency')))
            os_amount = self._compute_amount_total_currency_signed(options,  move_line)
            amount_total = total
            running_total.append(os_amount)

            invoice_date = move.date
            invoice_due_date = move.invoice_date_due or move.date
            records = {
                'id': move.id,
                'title': move.name,
                'code': move.id,
                'level': 2,
                'row_class': 'font-weight-normal',
                'move_id': move.id,
                'group_by': False,
                'date': invoice_date,
                'due_date': invoice_due_date,
                'values': {
                    'Date': format_date(self.env, invoice_date),
                    'Voucher Number': (move.name),
                    'Narration': self.get_narration_from_house(move) or self._html_to_text(move.ref or move.narration or ''),
                    'Due date': format_date(self.env, invoice_due_date),
                    'Amount': (amount_total, self._format_currency(amount_total, currency=move.currency_id)),
                    'O/S Amount {}'.format(home_currency_code): (os_amount, self._format_currency(os_amount)),
                    'Running Total': (sum(running_total), self._format_currency(sum(running_total))),
                    'Ageing': self.get_count_days(invoice_due_date, options.get('date').get('date_to')),
                }}
            line_data.append(records)

        # NO SORTING, as records are sorted based on dates from move line
        return self.get_sorted(options, line_data, True)

    def get_narration_from_house(self, move_id):
        house_list = []
        for house in move_id.house_shipment_ids.sudo():
            opportunity_id = house.shipment_quote_id and house.shipment_quote_id.opportunity_id
            narration = ''
            if opportunity_id:
                narration = opportunity_id.sudo().name + '-'
            if house.hbl_number:
                narration += house.hbl_number
            if house.origin_port_un_location_id:
                narration += ' : ' + house.origin_port_un_location_id.code
            if house.destination_port_un_location_id:
                narration += ' - ' + house.destination_port_un_location_id.code
            if house.service_mode_id:
                narration += ' ' + f'({house.service_mode_id.name})'
            house_list.append(narration)
        narration_string = ", ".join(rec for rec in house_list)
        return narration_string

    def action_open_payment(self, move_id, options, **kwargs):
        action = self.env["ir.actions.act_window"]._for_xml_id("account.action_account_payments")
        form_view = [(self.env.ref('account.view_account_payment_form').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        action['res_id'] = move_id
        return action
