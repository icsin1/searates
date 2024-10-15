# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.tools import format_date


class OperationCustomerSaleReport(models.Model):
    _name = 'operation.custom.duty.report'
    _inherit = 'account.finance.report.mixin'
    _description = 'Operation: Custom Duty Report'

    def get_title(self):
        return _('Custom Duty Report')

    def get_report_action(self, options=False):
        return self.env.ref('fm_operation_reports.action_custom_duty_report')

    def get_account_report_data(self, options, **kwargs):
        self.has_date_range = True
        values = super().get_account_report_data(options, **kwargs)
        values['sections'] = self.get_sorted(options, self._get_sections(options, **kwargs))
        return values

    def _get_options(self, options, **kwargs):
        options = super()._get_options(options, **kwargs)
        options['sortable'] = True
        options['filters'] = {
            'partner_ids': {
                'string': _('Customer'),
                'res_model': 'res.partner',
                'res_field': 'partner_ids',
                'res_ids': options.get('partner_ids', [])
            }
        }
        return options

    def _get_column_headers(self, options, **kwargs):
        report_header = [
            _('Houseshipment No'),
            _('Vendor Name'),
            _('Billing Status'),
            _('Bill Number'),
            _('Vendor bill payment status'),
            _('Paid from which Bank'),
            _('Customer Name'),
            _('Invoice Status'),
            _('Invoice Number'),
            _('Invoice payment status'),
            _('Received from which Bank'),
            _('Paid Amount'),
            _('Received Amount'),
            _('Balance'),
        ]
        if hasattr(self.env['account.move'], 'x_internal_reference'):
            report_header.insert(4, _('Vendor Bill Number'))
        return report_header

    def _generate_domain(self, options, **kwargs):
        dates = options.get('date', {})
        date_to = dates.get('date_to', fields.Date().today())
        date_from = dates.get('date_from', fields.Date.start_of(fields.Date.from_string(date_to), 'year'))
        domain = [('create_date', '>=', date_from), ('create_date', '<=', date_to)]
        custom_duty_charge_ids = self.env.company.custom_duty_charge_ids
        domain += [('product_id', 'in', custom_duty_charge_ids.ids)]
        return domain

    def get_common_charges(self, charge):
        res = self.get_revenue_charges(charge)
        res.update(self.get_cost_charges(charge.cost_line_id))
        balance = res.get('Paid Amount', [0])[0] - res.get('Received Amount', [0])[0]
        res.update({
            'Balance': (balance, self._format_currency(balance)),
        })
        return res

    def get_cost_charges(self, record):
        bill_status = dict(record._fields['status'].selection).get(record.status)
        res = {
            'Houseshipment No': (record.house_shipment_id.id, record.house_shipment_id.booking_nomination_no),
            'Vendor Name': (record.partner_id.id, record.partner_id.display_name),
            'Billing Status': (bill_status, bill_status),
            'Bill Number': '',
            'Vendor bill payment status': '',
            'Paid from which Bank': '',
        }
        if record.move_line_ids:
            bill_ids = record.move_line_ids.mapped('move_id').filtered(lambda move: move.state != 'cancel')
            if bill_ids:
                res.update({
                    'Bill Number': ('', ','.join(bill_ids.mapped('name'))),
                })
                if hasattr(bill_ids, 'x_internal_reference'):
                    internal_ref_list = [move.x_internal_reference for move in bill_ids if move.x_internal_reference ]
                    res.update({
                        'Vendor Bill Number': ('', ','.join(internal_ref_list)),
                    })
                payment_status_list = bill_ids.mapped('payment_state')
                payment_status = dict(bill_ids[0]._fields['payment_state'].selection).get('not_paid')
                if 'partial' in payment_status_list:
                    payment_status = dict(bill_ids[0]._fields['payment_state'].selection).get('partial')
                elif 'in_payment' in payment_status_list:
                    payment_status = dict(bill_ids[0]._fields['payment_state'].selection).get('in_payment')
                elif 'paid' in payment_status_list:
                    payment_status = dict(bill_ids[0]._fields['payment_state'].selection).get('paid')
                res.update({
                    'Vendor bill payment status': (payment_status, payment_status),
                })
                payment_ids = self.env['account.payment']
                amount_paid = 0
                for move in bill_ids:
                    payment_ids |= move._get_reconciled_payments()
                    reconciled_vals = move._get_reconciled_info_JSON_values()
                    for rec in reconciled_vals:
                        if move.currency_id != self.env.company.currency_id:
                            amount_paid += move.currency_id.with_context(currency_exchange_rate=move.currency_exchange_rate)._convert(
                                rec.get('amount'),
                                self.env.company.currency_id,
                                self.env.company,
                                move.date,
                            )
                        else:
                            amount_paid += rec.get('amount')
                receive_bank = ','.join(payment_ids.mapped('journal_id.name'))
                res.update({
                    'Paid from which Bank': (receive_bank, receive_bank),
                    'Paid Amount': (amount_paid, self._format_currency(amount_paid)),
                })
                balance = amount_paid
                res.update({
                    'Balance': (balance, self._format_currency(balance)),
                })
        return res

    def get_revenue_charges(self, record):
        invoice_status = dict(record._fields['status'].selection).get(record.status)
        res = {
            'Houseshipment No': (record.house_shipment_id.id, record.house_shipment_id.booking_nomination_no),
            'Customer Name': (record.partner_id.id, record.partner_id.display_name),
            'Invoice Status': (invoice_status, invoice_status),
            'Invoice Number': '',
            'Invoice payment status': '',
            'Received from which Bank': '',
        }
        if record.move_line_ids:
            invoice_ids = record.move_line_ids.mapped('move_id').filtered(lambda move: move.state != 'cancel')
            if invoice_ids:
                res.update({
                    'Invoice Number': ('', ','.join(invoice.name or '/' for invoice in invoice_ids)),
                })
                payment_status_list = invoice_ids.mapped('payment_state')
                payment_status = dict(invoice_ids[0]._fields['payment_state'].selection).get('not_paid')
                if 'partial' in payment_status_list:
                    payment_status = dict(invoice_ids[0]._fields['payment_state'].selection).get('partial')
                elif 'in_payment' in payment_status_list:
                    payment_status = dict(invoice_ids[0]._fields['payment_state'].selection).get('in_payment')
                elif 'paid' in payment_status_list:
                    payment_status = dict(invoice_ids[0]._fields['payment_state'].selection).get('paid')
                res.update({
                    'Invoice payment status': (payment_status, payment_status),
                })
                payment_ids = self.env['account.payment']
                amount_paid = 0
                for move in invoice_ids:
                    payment_ids |= move._get_reconciled_payments()
                    reconciled_vals = move._get_reconciled_info_JSON_values()
                    for rec in reconciled_vals:
                        if move.currency_id != self.env.company.currency_id:
                            amount_paid += move.currency_id.with_context(currency_exchange_rate=move.currency_exchange_rate)._convert(
                                rec.get('amount'),
                                self.env.company.currency_id,
                                self.env.company,
                                move.date,
                            )
                        else:
                            amount_paid += rec.get('amount')
                receive_bank = ','.join(payment_ids.mapped('journal_id.name'))
                res.update({
                    'Received from which Bank': (receive_bank, receive_bank),
                    'Received Amount': (amount_paid, self._format_currency(amount_paid)),
                })
                balance = amount_paid
                res.update({
                    'Balance': (balance, self._format_currency(balance)),
                })
        return res

    def _get_charge_values(self, res_model, domain, fields, group_by_fields):
        return self.env[res_model].sudo().search(domain, order="partner_id, house_shipment_id")

    def get_default_values(self):
        values = {
            'Houseshipment No': '',
            'Vendor Name': '',
            'Billing Status': '',
            'Bill Number': '',
            'Vendor bill payment status': '',
            'Paid from which Bank': '',
            'Customer Name': '',
            'Invoice Status': '',
            'Invoice Number': '',
            'Invoice payment status': '',
            'Received from which Bank': '',
            'Paid Amount': (0.00, self._format_currency(0.00)),
            'Received Amount': (0.00, self._format_currency(0.00)),
            'Balance': (0.00, self._format_currency(0.00)),
        }
        if hasattr(self.env['account.move'], 'x_internal_reference'):
            values['Vendor Bill Number'] = ''
        return values

    def _get_column_headers_properties(self, options, **kwargs):
        return {
            'Houseshipment No': {'sortable': True},
            'Vendor Name': {'sortable': True},
            'Customer Name': {'sortable': True},
        }

    def _get_sections(self, options, **kwargs):
        data = []
        company_ids = self.env.context.get('allowed_company_ids', [])
        partner_domain = [
            ('partner_id', '!=', False),
            ('company_id', 'in', company_ids),
        ]
        data_domain = partner_domain + self._generate_domain(options, **kwargs)
        if options.get('partner_ids'):
            data_domain += [('partner_id', 'in', options.get('partner_ids'))]
        revenue_records = self._get_charge_values('house.shipment.charge.revenue', data_domain, ['partner_id'],
                                                  ['partner_id'])
        cost_records = self._get_charge_values('house.shipment.charge.cost', data_domain, ['partner_id'], ['partner_id'])
        common_records = revenue_records.filtered(lambda charge: charge.cost_line_id)
        revenue_records = revenue_records - common_records
        cost_records = cost_records - common_records.mapped('cost_line_id')
        partner_ids = revenue_records.mapped('partner_id.id') + cost_records.mapped('partner_id.id') + common_records.mapped('partner_id.id')
        partner_ids = self.env['res.partner'].browse(list(set(partner_ids)))
        for partner in partner_ids:
            common_charges = common_records.filtered(lambda common_charge: common_charge.partner_id.id == partner.id)
            for charge in common_charges:
                values = self.get_default_values()
                values.update(self.get_common_charges(charge))
                data.append({
                    'id': partner.id,
                    'title': '',
                    'code': partner.id,
                    'level': 1,
                    'group_by': False,
                    'row_class': 'font-weight-normal',
                    'values': values,
                })
            revenue_charges = revenue_records.filtered(lambda revenue_charge: revenue_charge.partner_id == partner)
            for charge in revenue_charges:
                values = self.get_default_values()
                values.update(self.get_revenue_charges(charge))
                data.append({
                    'id': partner.id,
                    'title': '',
                    'code': partner.id,
                    'level': 1,
                    'group_by': False,
                    'row_class': 'font-weight-normal',
                    'values': values,
                })
            cost_charges = cost_records.filtered(
                lambda cost_charge: cost_charge.partner_id == partner)
            for charge in cost_charges:
                values = self.get_default_values()
                values.update(self.get_cost_charges(charge))
                data.append({
                    'id': partner.id,
                    'title': '',
                    'code': partner.id,
                    'level': 1,
                    'group_by': False,
                    'row_class': 'font-weight-normal',
                    'values': values,
                })
        return self.get_sorted(options, data, True)

    def get_account_report_section_data(self, parent, options, **kwargs):
        return []

    def action_print_report_xlsx_summary(self, options, **kwargs):
        action = super().action_print_report_xlsx_summary(options, **kwargs)
        action['data']['folded'] = False
        return action

    def excel_write_report_lines(self, workbook, worksheet, options, row):
        bold_right_text = workbook.add_format({'align': 'right', 'valign': 'vcenter', 'bold': True})
        bold_left_text = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'bold': True})
        total_left_text = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'bold': True, 'top': 2})
        total_right_text = workbook.add_format({'align': 'right', 'valign': 'vcenter', 'bold': True, 'top': 2})
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
                    vals = line['values'][line_key]
                    vals = tuple(vals)[1] if isinstance(vals, tuple) else vals
                worksheet.write(row, column, vals, style)
                column += 1
            row += 1
            if self._name == 'account.finance.report' and line['children']:
                row = self.excel_add_section_children(workbook, worksheet, options, row, line)
            if self._name != 'account.finance.report' and line['id'] != 'total' and not options.get('folded'):
                for detail_line in self.get_account_report_section_data(line, options):
                    row = self.excel_add_section_line(workbook, worksheet, row, detail_line)
        return worksheet, row
