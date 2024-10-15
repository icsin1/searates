# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.tools import format_date


class AccountWithholdingTaxReport(models.Model):
    _name = 'account.withholding.tax.report'
    _inherit = 'account.finance.report.mixin'
    _description = 'Account Withholding Tax Report'

    def get_title(self):
        return _('Withholding Tax Report')

    def get_account_report_data(self, options, **kwargs):
        self.has_date_range = True
        values = super().get_account_report_data(options, **kwargs)
        values['sections'] = self.get_sorted(options, self._get_sections(options, **kwargs))
        return values

    def _get_column_headers(self, options, **kwargs):
        report_header = [
            _('S/No'),
            _('Batch Name'),
            _('Tin Of Withholdee'),
            _('Name of Withholdee'),
            _('Withholding Tax Rate'),
            _('Amount Exclusive of VAT'),
            _('Withholding Tax Due'),
            _('Date of Deduction')
        ]
        return report_header

    def _generate_domain(self, options, **kwargs):
        dates = options.get('date', {})
        domain = []
        if not dates:
            return domain
        domain += [('date', '>=', dates.get('date_from')), ('date', '<=', dates.get('date_to'))]
        return domain

    def _get_sections(self, options, **kwargs):
        data = []
        company_ids = self.env.context.get('allowed_company_ids', [])
        vendor_payment_domain = [('partner_id', '!=', False), ('company_id', 'in', company_ids), ('state', '=', 'posted'),
                                 ('partner_type', '=', 'supplier'), ('is_internal_transfer', '=', False), ('withholding_tax_id', '!=', False)]
        data_domain = vendor_payment_domain + self._generate_domain(options, **kwargs)
        vendor_payment_ids = self.env['account.payment'].search(data_domain)
        sr_no = 1
        batch_name = options.get('date') and options.get('date').get('string') or ''
        amount_exclusive_of_vat_amount = 0.00
        withholding_tax_due_amount = 0.00
        for payment in vendor_payment_ids:
            tax_amount = abs(sum(payment.line_ids.filtered(lambda move_line: move_line.withholding_tax_line).mapped('balance')))
            liquidity_lines_payment = abs(payment.amount_company_currency_signed)
            total_payment_amount = liquidity_lines_payment + tax_amount
            amount_exclusive_of_vat_amount += total_payment_amount
            withholding_tax_due_amount += tax_amount
            data.append({
                'id': payment.id,
                'title': '',
                'code': payment.id,
                'level': 1,
                'group_by': False,
                'row_class': 'font-weight-normal',
                'values': {
                    'S/No': (sr_no, sr_no),
                    'Batch Name': (batch_name, batch_name),
                    'Tin Of Withholdee': (payment.partner_id.l10n_tz_tin or '', payment.partner_id.l10n_tz_tin or ''),
                    'Name of Withholdee': (payment.partner_id.name, payment.partner_id.name),
                    'Withholding Tax Rate': (abs(payment.withholding_tax_id.amount), abs(payment.withholding_tax_id.amount)),
                    'Amount Exclusive of VAT': (self._format_currency(total_payment_amount), self._format_currency(total_payment_amount)),
                    'Withholding Tax Due': (self._format_currency(tax_amount), self._format_currency(tax_amount)),
                    'Date of Deduction': (format_date(self.env, payment.date), format_date(self.env, payment.date))
                },
            })
            sr_no += 1

        data.append({
            'id': 'total',
            'title': _('Total'),
            'code': 'total',
            'level': 0,
            'group_by': False,
            'values': {
                'S/No': ('', ''),
                'Batch Name': ('', ''),
                'Tin Of Withholdee': ('', ''),
                'Name of Withholdee': ('', ''),
                'Withholding Tax Rate': ('', ''),
                'Amount Exclusive of VAT': (self._format_currency(amount_exclusive_of_vat_amount), self._format_currency(amount_exclusive_of_vat_amount)),
                'Withholding Tax Due': (self._format_currency(withholding_tax_due_amount), self._format_currency(withholding_tax_due_amount)),
                'Date of Deduction': ('', '')
                },
        })
        return self.get_sorted(options, data, True)
