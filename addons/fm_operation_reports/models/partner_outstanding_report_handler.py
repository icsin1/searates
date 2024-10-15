import re
from odoo import models, fields, _


class PartnerOutstandingStatementHandler(models.AbstractModel):
    _name = 'partner.outstanding.statement.report'
    _description = 'Partner Outstanding Report Handler'
    _inherit = ['mixin.report.handler']

    def _get_report_filename(self, report, options, **kwargs):
        return self.get_title(report, options, **kwargs)

    def _get_report_title(self, report):
        report_label = _('Customer') if report.env.context.get('report_type') == 'receivable' else _('Vendor')
        return _(f'Outstanding {report_label} Statement Report')

    def get_title(self, report, options, **kwargs):
        report_label = _('Customer') if report.env.context.get('report_type') == 'receivable' else _('Vendor')
        return _(f'Outstanding {report_label} Statement Report')

    def _get_filter_label(self, report_filter, options, **kwargs):
        name = super()._get_filter_label(report_filter, options, **kwargs)
        if report_filter.filter_key == 'filter_customers':
            return _('Customer') if self.env.context.get('report_type') == 'receivable' else _('Vendor')
        if report_filter.filter_key == 'filter_based_on':
            choice_ids = report_filter.choice_ids
            option_value = options.get('dynamic_filter_search', {}).get(report_filter.filter_key)
            default_choice = choice_ids.filtered(lambda choice: option_value and (choice.choice_key == option_value))
            if not default_choice:
                default_choice = choice_ids.filtered(lambda choice: choice.is_default)
            return "{} {}".format(report_filter.name, default_choice and self._get_choice_label(default_choice[0]) or '')
        return name

    def _get_choice_label(self, choice):
        if choice.choice_key == 'date':
            return _('Invoice Date') if self.env.context.get('report_type') == 'receivable' else _('Bill Date')
        return choice.name

    def _report_handler_partner_outstanding_report_data(self, report, report_line, record, domain, options, report_group, group_by, report_group_key, previous_record, **kwargs):
        values = {
            'narration': '',
            'amount': 0,
            'os_amount': 0,
            'running_total': 0,
            'ageing': 0
        }
        self = self.with_context(prefetch_fields=False)
        is_not_group_total = False
        if record.get('__domain'):
            move_lines = self.env['account.move.line'].search(record.get('__domain'))
            moves = move_lines.mapped("move_id")

            os_amount = self._compute_amount_total_currency_signed(options,  move_lines)
            is_not_group_total = not kwargs.get('group_total') and group_by == 'id'

            values.update({
                'os_amount': os_amount,
                'running_total': os_amount,
                'amount': self._get_amount_total(options, move_lines) if is_not_group_total else 0
            })

        if is_not_group_total:
            aging_based_on = options.get("dynamic_filter_search").get("filter_based_on", 'due_date')
            date_field = 'date_maturity' if aging_based_on == 'due_date' else 'invoice_date'
            ageing = self._get_count_days(options, record.get(date_field) or moves.date)
            previous_running_total = previous_record and previous_record.get('values', {}).get(report_group_key, {}).get('running_total_original', 0)
            values.update({
                'narration': self._get_narration_from_house(moves) or self._html_to_text(
                    ','.join([ref for ref in moves.mapped('ref') if ref]) or ','.join(nar for nar in moves.mapped('narration') if nar) or ''),
                'os_amount': os_amount,
                'running_total': os_amount + (previous_running_total or 0),
                'ageing': ageing,
                'date': moves.date,
                'invoice_date': moves.invoice_date or moves.date
            })

        return values

    def _get_handler_domain(self, report, options, **kwargs):
        domain = super()._get_handler_domain(report, options, **kwargs)
        date_to = options.get('filter_date_options').get('date_to')
        domain += [
            '|', ('reconciled', '=', False),
            '|', ('matched_debit_ids.max_date', '>', date_to), ('matched_credit_ids.max_date', '>', date_to)]
        return domain

    def _html_to_text(self, html_value):
        # Removing <br> with \n
        html_value = str(html_value or '').replace("<br>", "\n")
        # and removing all HTML tags
        return re.sub(r'<[^<]+?>', '', html_value)

    def _get_narration_from_house(self, move_id):
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

    def _get_amount_total(self, options, move_line):
        date_to = options.get('filter_date_options').get('date_to')
        part_debit = move_line.matched_debit_ids.filtered_domain([('max_date', '<=', date_to)])
        part_credit = move_line.matched_credit_ids.filtered_domain([('max_date', '<=', date_to)])

        credit_amount = sum(part_credit.mapped('debit_amount_currency'))
        debit_amount = sum(part_debit.mapped('credit_amount_currency'))

        reconciled_amount = credit_amount - debit_amount
        amount_currency = sum(move_line.mapped('amount_currency'))

        return amount_currency - reconciled_amount

    def _compute_amount_total_currency_signed(self, options, move_line_ids):
        date_to = options.get('filter_date_options').get('date_to')
        self = self.with_context(prefetch_fields=False)
        domain = [('max_date', '<=', date_to)]

        credit_amount = sum(move_line_ids.matched_credit_ids.filtered_domain(domain).mapped('amount'))
        debit_amount = sum(move_line_ids.matched_debit_ids.filtered_domain(domain).mapped('amount'))

        amount_currency = sum(move_line_ids.mapped("balance"))
        reconciled_amount_currency = credit_amount - debit_amount

        return amount_currency - reconciled_amount_currency

    def _get_count_days(self, options, from_day):
        to_day = options.get('filter_date_options').get('date_to')
        start_day = fields.Date.from_string(from_day)
        end_day = fields.Date.from_string(to_day)
        return (end_day - start_day).days
