# -*- coding: utf-8 -*-
import io
import xlsxwriter
import base64

from odoo import models, fields, _, api
from odoo.exceptions import UserError


class VATReturn(models.Model):
    _name = "vat.return"
    _description = "Vat Return"

    name = fields.Char('Name', compute="_compute_vat_name")
    from_date = fields.Date('From')
    to_date = fields.Date('To')
    vat_return_sale_ids = fields.One2many('vat.return.sale.line', 'vat_return_id', string="Vat Sale Lines")
    vat_return_purchase_ids = fields.One2many('vat.return.purchase.line', 'vat_return_id', string="Vat Purchase Lines")
    vat_return_summary_ids = fields.One2many('vat.return.summary.line', 'vat_return_id', string="Vat Summary Lines")
    sale_tax_vat_amount_total = fields.Float('Total Of VAT Tax', default=0.0, compute="_compute_sale_tax_amount_total")
    total_of_adjustment = fields.Float('Adjustment Amount Total', default=0.0, compute="_compute_sale_tax_amount_total")
    total_recoverable_vat_amount = fields.Float('Total of Purchase', default=0.0, compute="_compute_purchase_tax_amount_total")
    total_of_purchase_adjustment = fields.Float('Total of Purchase Adjustment', default=0.0, compute="_compute_purchase_tax_amount_total")
    total_value_of_due_tax = fields.Float('Total value of due tax for the period', default=0.0, compute="_compute_total_value_of_due_tax")
    total_of_recoverable_tax = fields.Float('Total value of recoverable tax for the period', default=0.0, compute="_compute_total_value_of_recoverable_tax")
    net_payable_amount = fields.Float('Total Net Payable', default=0.0, compute="_compute_net_payable_amount")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id)
    partner_ids = fields.Many2many('res.partner', string="Customers")

    def _compute_vat_name(self):
        for record in self:
            name = 'VAT 201 Return Report'
            if record.from_date and record.to_date:
                name = '%s (%s-%s)' % (name, record.from_date, record.to_date)
                record.name = name

    @api.depends('vat_return_sale_ids')
    def _compute_sale_tax_amount_total(self):
        for record in self:
            sale_tax_amount_total = 0.0
            total_of_adjustment = 0.0
            for line in record.vat_return_sale_ids:
                sale_tax_amount_total += line.actual_tax_amount
                total_of_adjustment += line.adjustment_amount
            record.sale_tax_vat_amount_total = sale_tax_amount_total
            record.total_of_adjustment = total_of_adjustment

    @api.depends('vat_return_purchase_ids')
    def _compute_purchase_tax_amount_total(self):
        for record in self:
            total_recoverable_vat_amount = 0.0
            total_of_adjustment = 0.0
            for line in record.vat_return_purchase_ids:
                total_recoverable_vat_amount += line.actual_tax_amount
                total_of_adjustment += line.adjustment_amount
            record.total_recoverable_vat_amount = total_recoverable_vat_amount
            record.total_of_purchase_adjustment = total_of_adjustment

    @api.depends('sale_tax_vat_amount_total', 'total_of_adjustment')
    def _compute_total_value_of_due_tax(self):
        for record in self:
            record.total_value_of_due_tax = record.sale_tax_vat_amount_total + record.total_of_adjustment

    @api.depends('total_recoverable_vat_amount', 'total_of_purchase_adjustment')
    def _compute_total_value_of_recoverable_tax(self):
        for record in self:
            record.total_of_recoverable_tax = record.total_recoverable_vat_amount + record.total_of_purchase_adjustment

    @api.depends('total_value_of_due_tax', 'total_of_recoverable_tax')
    def _compute_net_payable_amount(self):
        for record in self:
            record.net_payable_amount = record.total_value_of_due_tax - record.total_of_recoverable_tax

    def _prepare_tax_data_list(self):
        sale_tax_data_list = [
            {
                'box': '1a',
                'description': 'Standard rated supplies in Abu Dhabi',
                'amount_tag_name': ['+a. Abu Dhabi (Base)'],
                'amount_vat_tag_name': ['+a. Abu Dhabi (Tax)'],
                'credit_vat_base': ['-a. Abu Dhabi (Base)'],
                'debit_note_tax': ['-a. Abu Dhabi (Tax)'],
                'amount_base': 0.0,
                'amount_tax': 0.0,
                'adjustment_amount': 0.0
            },
            {
                'box': '1b',
                'description': 'Standard rated supplies in Dubai',
                'amount_tag_name': ['+b. Dubai (Base)'],
                'amount_vat_tag_name': ['+b. Dubai (Tax)'],
                'credit_vat_base': ['-b. Dubai (Base)'],
                'debit_note_tax': ['-b. Dubai (Tax)'],
                'amount_base': 0.0,
                'amount_tax': 0.0,
                'adjustment_amount': 0.0
            },
            {
                'box': '1c',
                'description': 'Standard rated supplies in Sharjah',
                'amount_tag_name': ['+c. Sharjah (Base)'],
                'amount_vat_tag_name': ['+c. Sharjah (Tax)'],
                'credit_vat_base': ['-c. Sharjah (Base)'],
                'debit_note_tax': ['-c. Sharjah (Tax)'],
                'amount_base': 0.0,
                'amount_tax': 0.0,
                'adjustment_amount': 0.0
            },
            {
                'box': '1d',
                'description': 'Standard rated supplies in Ajman',
                'amount_tag_name': ['+d. Ajman (Base)'],
                'amount_vat_tag_name': ['+d. Ajman (Tax)'],
                'credit_vat_base': ['-d. Ajman (Base)'],
                'debit_note_tax': ['-d. Ajman (Tax)'],
                'amount_base': 0.0,
                'amount_tax': 0.0,
                'adjustment_amount': 0.0
            },
            {
                'box': '1e',
                'description': 'Standard rated supplies in Umm Al Quwain',
                'amount_tag_name': ['+e. Umm Al Quwain (Base)'],
                'amount_vat_tag_name': ['+e. Umm Al Quwain (Tax)'],
                'credit_vat_base': ['-e. Umm Al Quwain (Base)'],
                'debit_note_tax': ['-e. Umm Al Quwain (Tax)'],
                'amount_base': 0.0,
                'amount_tax': 0.0,
                'adjustment_amount': 0.0
            },
            {
                'box': '1f',
                'description': 'Standard rated supplies in Ras Al Khaimah',
                'amount_tag_name': ['+f. Ras Al-Khaima (Base)'],
                'amount_vat_tag_name': ['+f. Ras Al-Khaima (Tax)'],
                'credit_vat_base': ['-f. Ras Al-Khaima (Base)'],
                'debit_note_tax': ['-f. Ras Al-Khaima (Tax)'],
                'amount_base': 0.0,
                'amount_tax': 0.0,
                'adjustment_amount': 0.0
            },
            {
                'box': '1g',
                'description': 'Standard rated supplies in Fujairah',
                'amount_tag_name': ['+g. Fujairah (Base)'],
                'amount_vat_tag_name': ['+g. Fujairah (Tax)'],
                'credit_vat_base': ['-g. Fujairah (Base)'],
                'debit_note_tax': ['-g. Fujairah (Tax)'],
                'amount_base': 0.0,
                'amount_tax': 0.0,
                'adjustment_amount': 0.0
            },
            {
                'box': '2',
                'description': 'Tax Refunds provided to Tourists under the Tax Refunds for Tourists Scheme',
                'amount_tag_name': ['+2. Tax Refunds provided to Tourists under the Tax Refunds for Tourists Scheme (Base)'],
                'amount_vat_tag_name': ['+2. Tax Refunds provided to Tourists under the Tax Refunds for Tourists Scheme (Tax)'],
                'credit_vat_base': ['-2. Tax Refunds provided to Tourists under the Tax Refunds for Tourists Scheme (Base)'],
                'debit_note_tax': ['-2. Tax Refunds provided to Tourists under the Tax Refunds for Tourists Scheme (Tax)'],
                'amount_base': 0.0,
                'amount_tax': 0.0,
                'adjustment_amount': 0.0
            },
            {
                'box': '3',
                'description': 'Supplies subject to the reverse charge provisions',
                'amount_tag_name': ['+3. Supplies subject to reverse charge provisions (Base)'],
                'amount_vat_tag_name': ['-3. Supplies subject to reverse charge provisions (Tax)'],
                'credit_vat_base': ['-3. Supplies subject to reverse charge provisions (Base)'],
                'debit_note_tax': ['+3. Supplies subject to reverse charge provisions (Tax)'],
                'amount_base': 0.0,
                'amount_tax': 0.0,
                'adjustment_amount': 0.0
            },
            {
                'box': '4',
                'description': 'Zero rated supplies',
                'amount_tag_name': ['+4. Zero rated supplies (Base)'],
                'amount_vat_tag_name': [],
                'credit_vat_base': ['-4. Zero rated supplies (Base)'],
                'debit_note_tax': [],
                'amount_base': 0.0,
                'amount_tax': 0.0,
                'adjustment_amount': 0.0
            },
            {
                'box': '5',
                'description': 'Exempt supplies',
                'amount_tag_name': ['+5. Exempt supplies (Base)'],
                'amount_vat_tag_name': [],
                'credit_vat_base': ['-5. Exempt supplies (Base)'],
                'debit_note_tax': [],
                'amount_base': 0.0,
                'amount_tax': 0.0,
                'adjustment_amount': 0.0
            },
            {
                'box': '6',
                'description': 'Goods imported into the UAE',
                'amount_tag_name': ['+7. Goods imported into the UAE (Base)'],
                'amount_vat_tag_name': ['+7. Goods imported into the UAE (Tax)'],
                'credit_vat_base': ['-7. Goods imported into the UAE (Base)'],
                'debit_note_tax': ['-7. Goods imported into the UAE (Tax)'],
                'amount_base': 0.0,
                'amount_tax': 0.0,
                'adjustment_amount': 0.0
            },
            {
                'box': '7',
                'description': 'Adjustments and additions to goods imported into the UAE',
                'amount_tag_name': [],
                'amount_vat_tag_name': [],
                'credit_vat_base': [],
                'debit_note_tax': [],
                'amount_base': 0.0,
                'amount_tax': 0.0,
                'adjustment_amount': 0.0
            },
        ]
        purchase_tax_data_list = [
            {
                'box': '9',
                'description': 'Standard rated expenses',
                'amount_tag_name': ['+10. Standard rated expenses (Base)'],
                'amount_vat_tag_name': ['+10. Standard rated expenses (Tax)'],
                'credit_vat_base': ['-10. Standard rated expenses (Base)'],
                'debit_note_tax': ['-10. Standard rated expenses (Tax)'],
                'amount_base': 0.0,
                'amount_tax': 0.0,
                'adjustment_amount': 0.0
            },
            {
                'box': '10',
                'description': 'Supplies subject to the reverse charge provisions',
                'amount_tag_name': ['+11. Supplies subject to the reverse charge provisions (Base)'],
                'amount_vat_tag_name': ['+11. Supplies subject to the reverse charge provisions (Tax)'],
                'credit_vat_base': ['-11. Supplies subject to the reverse charge provisions (Base)'],
                'debit_note_tax': ['-11. Supplies subject to the reverse charge provisions (Tax)'],
                'amount_base': 0.0,
                'amount_tax': 0.0,
                'adjustment_amount': 0.0
            },
        ]
        return sale_tax_data_list, purchase_tax_data_list

    def fetch_tax_information(self):
        sale_tax_data_list, purchase_tax_data_list = self._prepare_tax_data_list()
        keep_adj_amt = self._context.get('keep_amount') or False
        sale_return_adjustment_amount = {}
        purchase_return_adjustment_amount = {}
        old_base_amount = 0.0
        old_tax_amount = 0.0
        for sale_line in self.vat_return_sale_ids:
            if keep_adj_amt:
                sale_return_adjustment_amount[sale_line.box_no] = sale_line.adjustment_amount
            if keep_adj_amt and sale_line.box_no == '7':
                old_base_amount = sale_line.actual_base_amount
                old_tax_amount = sale_line.actual_tax_amount
            sale_line.unlink()

        for purchase_line in self.vat_return_purchase_ids:
            if keep_adj_amt:
                purchase_return_adjustment_amount[purchase_line.box_no] = purchase_line.adjustment_amount

            purchase_line.unlink()

        for data in sale_tax_data_list:
            adj_amount = sale_return_adjustment_amount[data.get('box')] if data.get('box') in sale_return_adjustment_amount else 0.0

            # for getting tax info in lines
            sales_tags = data.get('amount_tag_name') + data.get('amount_vat_tag_name') + data.get('credit_vat_base') + data.get('debit_note_tax')

            sale_line = self.env['vat.return.sale.line'].create({
                'vat_return_id': self.id,
                'box_no': data.get('box'),
                'description': data.get('description'),
                'base_amount': self.get_tax_information_from_tag(data.get('amount_tag_name')) or 0.0,
                'tax_amount': self.get_tax_information_from_tag(data.get('amount_vat_tag_name')) or 0.0,
                'credit_amount': self.get_tax_information_from_tag(data.get('credit_vat_base')) or 0.0,
                'debit_amount': self.get_tax_information_from_tag(data.get('debit_note_tax')) or 0.0,
                'adjustment_amount': adj_amount,
                'tag_ids': [(6, 0, self.get_tax_ids(sales_tags))],
            })
            if sale_line and data.get('box') == '2':
                sale_line.actual_tax_amount = - sale_line.actual_tax_amount
                sale_line.actual_base_amount = - sale_line.actual_base_amount
            if sale_line and data.get('box') == '7':
                sale_line.actual_base_amount = old_base_amount
                sale_line.actual_tax_amount = old_tax_amount

        for data in purchase_tax_data_list:
            adj_amount = purchase_return_adjustment_amount[data.get('box')] if data.get('box') in purchase_return_adjustment_amount else 0.0

            purchase_tags = data.get('amount_tag_name') + data.get('amount_vat_tag_name') + data.get('credit_vat_base') + data.get('debit_note_tax')

            self.env['vat.return.purchase.line'].create({
                'vat_return_id': self.id,
                'box_no': data.get('box'),
                'description': data.get('description'),
                'base_amount': self.get_tax_information_from_tag(data.get('amount_tag_name')) or 0.0,
                'tax_amount': self.get_tax_information_from_tag(data.get('amount_vat_tag_name')) or 0.0,
                'credit_amount': self.get_tax_information_from_tag(data.get('credit_vat_base')) or 0.0,
                'debit_amount': self.get_tax_information_from_tag(data.get('debit_note_tax')) or 0.0,
                'adjustment_amount': adj_amount,
                'tag_ids': [(6, 0, self.get_tax_ids(purchase_tags))],
            })

    def _get_account_move_lines_by_tag(self, tag):
        tax_tag = self.env['account.account.tag'].search([('name', '=', tag)], limit=1)
        if not tax_tag:
            raise UserError(_("%s Tax Tag not found") % tag)

        domain = [('date', '>=', self.from_date), ('date', '<=', self.to_date), ('parent_state', '=', 'posted'), ('tax_tag_ids', 'in', [tax_tag.id]), ('company_id', '=', self.env.company.id)]
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
        return self.env['account.move.line'].search(domain)

    # to get tax_tag_ids
    def get_tax_ids(self, tag_list):
        return self.env['account.account.tag'].search([('name', 'in', tag_list)]).ids

    def get_tax_information_from_tag(self, tag_list):
        amount = 0.0
        for tag in tag_list:
            move_line_obj_list = self._get_account_move_lines_by_tag(tag)
            for line in move_line_obj_list:
                amount = amount + abs(line.balance)
        return amount

    def action_print_pdf(self):
        self.ensure_one()
        return self.env.ref('l10n_ae_vat_return.action_vat_return_report').report_action(self)

    def get_header_style(self):
        return {
            'align': 'center',
            'bold': True,
            'font_size': '11',
            'bg_color': '#0070C0',
            'valign': 'vcenter',
            'font_color': 'white',
            'text_wrap': True,
        }

    def set_header_row(self, workbook, worksheet, header_list):
        heading_style = workbook.add_format(self.get_header_style())
        row_format = workbook.add_format({
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter'
        })
        header_row = 0
        for col, header in enumerate(header_list):
            worksheet.write(header_row, col, header, heading_style)
            worksheet.set_column(header_row, col, 15)
            worksheet.set_row(0, cell_format=row_format)

    def _get_account_move_lines_tax_details(self, tag):
        tax_tag = self.env['account.account.tag'].search([('name', '=', tag)], limit=1)
        if not tax_tag:
            raise UserError(_("%s Tax Tag not found") % tag)

        domain = [('date', '>=', self.from_date), ('date', '<=', self.to_date), ('parent_state', '=', 'posted'), ('tax_tag_ids', 'in', [tax_tag.id]), ('company_id', '=', self.env.company.id)]
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
        tax_details_query, tax_details_params = self.env['account.move.line']._get_query_tax_details_from_domain(domain)
        self.env.cr.execute(tax_details_query, tax_details_params)
        tax_details_res = self.env.cr.dictfetchall()
        return tax_details_res, tax_tag

    def worksheet_box1_data(self):
        sale_tax_data_list, purchase_tax_data_list = self._prepare_tax_data_list()
        box1_serial_nos = ['1a', '1b', '1c', '1d', '1e', '1f', '1g']
        data = []
        for serial_no in box1_serial_nos:
            sale_tax_data = list(filter(lambda item: item.get('box') == serial_no, sale_tax_data_list))
            sale_tax_data = sale_tax_data and sale_tax_data[0]
            tag_list = [sale_tax_data.get('amount_tag_name'), sale_tax_data.get('amount_vat_tag_name'), sale_tax_data.get('credit_vat_base'), sale_tax_data.get('debit_note_tax')]
            for tag in tag_list:
                if tag:
                    tax_details_res, tax_tag = self._get_account_move_lines_tax_details(tag[0])
                    sign = -1
                    for tax_detail in tax_details_res:
                        move_line = self.env['account.move.line'].browse(tax_detail.get('base_line_id'))
                        if move_line:
                            data.append({
                                'Serial #': serial_no,
                                'Tax Payer TRN': self.env.company.vat or '',
                                'Company Name / Member Company Name (If applicable)': self.env.company.name,
                                'Tax Invoice/Tax credit note  No': move_line.move_id.name,
                                'Tax Invoice/Tax credit note Date - DD/MM/YYYY format only': move_line.move_id.invoice_date.strftime("%d/%m/%Y") if move_line.move_id.invoice_date else '',
                                'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)': '{} to {}'.format(self.from_date.strftime("%d/%m/%Y"), self.to_date.strftime("%d/%m/%Y")),
                                'Tax Invoice/Tax credit note Amount AED (before VAT)': tax_detail.get('base_amount') * sign,
                                'VAT Amount AED': tax_detail.get('tax_amount') * sign,
                                'Customer Name': move_line.move_id.partner_id.name,
                                'Customer TRN': move_line.move_id.partner_id.vat or '',
                                'Clear description of the supply': move_line.name,
                                'VAT Adjustments (if any)': '',
                            })
        return data

    def worksheet_box1(self, workbook):
        worksheet = workbook.add_worksheet("Std Rated Sales - Box 1")
        header_list = ['Serial #', 'Tax Payer TRN', 'Company Name / Member Company Name (If applicable)', 'Tax Invoice/Tax credit note  No',
                       'Tax Invoice/Tax credit note Date - DD/MM/YYYY format only', 'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)',
                       'Tax Invoice/Tax credit note Amount AED (before VAT)', 'VAT Amount AED', 'Customer Name', 'Customer TRN', 'Clear description of the supply', 'VAT Adjustments (if any)']
        self.set_header_row(workbook, worksheet, header_list)
        worksheet_data = self.worksheet_box1_data()
        content_row = 1
        for data in worksheet_data:
            for col, value in data.items():
                column_index = header_list.index(col)
                worksheet.write(content_row, column_index, value)
            content_row += 1

    def worksheet_out_of_scope_sales(self, workbook):
        worksheet = workbook.add_worksheet("Out of scope Sales")
        header_list = ['Serial #', 'Tax Payer TRN', 'Company Name / Member Company Name (If applicable)', 'Tax Invoice/Tax credit note  No',
                       'Tax Invoice/Tax credit note Date - DD/MM/YYYY format only', 'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)',
                       'Tax Invoice/Tax credit note Amount AED (before VAT) ', 'VAT Amount AED ', 'Customer Name', 'Customer TRN', 'Clear description of the supply',
                       'Reason of Out-of-Scope Sales treatment']
        self.set_header_row(workbook, worksheet, header_list)

    def worksheet_box2_data(self):
        sale_tax_data_list, purchase_tax_data_list = self._prepare_tax_data_list()
        box2_serial_nos = ['2']
        data = []
        for serial_no in box2_serial_nos:
            sale_tax_data = list(filter(lambda item: item.get('box') == serial_no, sale_tax_data_list))
            sale_tax_data = sale_tax_data and sale_tax_data[0]
            tag_list = [sale_tax_data.get('amount_vat_tag_name'), sale_tax_data.get('debit_note_tax')]
            for tag in tag_list:
                if tag:
                    tax_details_res, tax_tag = self._get_account_move_lines_tax_details(tag[0])
                    for tax_detail in tax_details_res:
                        move_line = self.env['account.move.line'].browse(tax_detail.get('base_line_id'))
                        if move_line:
                            move = move_line.move_id
                            sign = -1 if move.move_type == 'out_refund' else 1
                            data.append({
                                'Invoice #': move.display_name,
                                'Tax Payer TRN': self.env.company.vat or '',
                                'Company Name / Member Company Name (If applicable)': self.env.company.name,
                                'Invoice Date - DD/MM/YYYY format only': move.invoice_date.strftime("%d/%m/%Y") if move.invoice_date else '',
                                'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)': '{} to {}'.format(self.from_date.strftime("%d/%m/%Y"), self.to_date.strftime("%d/%m/%Y")),
                                'Invoice Amount': move.amount_total * sign
                            })
        return data

    def worksheet_box2(self, workbook):
        worksheet = workbook.add_worksheet("Tourist Refund Adj - Box 2")
        header_list = ['Invoice #', 'Tax Payer TRN', 'Company Name / Member Company Name (If applicable)', 'Invoice Date - DD/MM/YYYY format only',
                       'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)', 'Invoice Amount']
        self.set_header_row(workbook, worksheet, header_list)
        worksheet_data = self.worksheet_box2_data()
        content_row = 1
        for data in worksheet_data:
            for col, value in data.items():
                column_index = header_list.index(col)
                worksheet.write(content_row, column_index, value)
            content_row += 1

    def worksheet_box3_data(self):
        sale_tax_data_list, purchase_tax_data_list = self._prepare_tax_data_list()
        box1_serial_nos = ['3']
        data = []
        for serial_no in box1_serial_nos:
            sale_tax_data = list(filter(lambda item: item.get('box') == serial_no, sale_tax_data_list))
            sale_tax_data = sale_tax_data and sale_tax_data[0]
            tag_list = [sale_tax_data.get('amount_tag_name'), sale_tax_data.get('amount_vat_tag_name'), sale_tax_data.get('credit_vat_base'), sale_tax_data.get('debit_note_tax')]
            for tag in tag_list:
                if tag:
                    tax_details_res, tax_tag = self._get_account_move_lines_tax_details(tag[0])
                    for tax_detail in tax_details_res:
                        move_line = self.env['account.move.line'].browse(tax_detail.get('base_line_id'))
                        if move_line:
                            sign = -1 if move_line.move_id.move_type in ['out_invoice', 'out_refund'] else 1
                            data.append({
                                'Serial #': serial_no,
                                'Tax Payer TRN': self.env.company.vat or '',
                                'Company Name / Member Company Name (If applicable)': self.env.company.name,
                                'Tax Invoice/Tax credit note No': move_line.move_id.name,
                                'Invoice/ credit note Date - DD/MM/YYYY format only': move_line.move_id.invoice_date.strftime("%d/%m/%Y") if move_line.move_id.invoice_date else '',
                                'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)': '{} to {}'.format(self.from_date.strftime("%d/%m/%Y"), self.to_date.strftime("%d/%m/%Y")),
                                'Invoice/credit note Amount AED (before VAT)': tax_detail.get('base_amount') * sign,
                                'VAT Amount AED': tax_detail.get('tax_amount') * -sign,
                                'Supplier Name': move_line.move_id.partner_id.name,
                                'Location of the Supplier': "{}, {}".format(move_line.move_id.partner_id.state_id.name or '', move_line.move_id.partner_id.country_id.name or ''),
                                'Clear description of the transaction': move_line.name,
                            })
        return data

    def worksheet_box3(self, workbook):
        worksheet = workbook.add_worksheet("Import of Services - Box 3")
        header_list = ['Serial #', 'Tax Payer TRN', 'Company Name / Member Company Name (If applicable)', 'Tax Invoice/Tax credit note No', 'Invoice/ credit note Date - DD/MM/YYYY format only',
                       'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)', 'Invoice/credit note Amount AED (before VAT)', 'VAT Amount AED', 'Supplier Name', 'Location of the Supplier',
                       'Clear description of the transaction']
        self.set_header_row(workbook, worksheet, header_list)
        worksheet_data = self.worksheet_box3_data()
        content_row = 1
        for data in worksheet_data:
            for col, value in data.items():
                column_index = header_list.index(col)
                worksheet.write(content_row, column_index, value)
            content_row += 1

    def worksheet_box4_data(self):
        sale_tax_data_list, purchase_tax_data_list = self._prepare_tax_data_list()
        box1_serial_nos = ['4']
        data = []
        for serial_no in box1_serial_nos:
            sale_tax_data = list(filter(lambda item: item.get('box') == serial_no, sale_tax_data_list))
            sale_tax_data = sale_tax_data and sale_tax_data[0]
            tag_list = [sale_tax_data.get('amount_tag_name'), sale_tax_data.get('amount_vat_tag_name'), sale_tax_data.get('credit_vat_base'), sale_tax_data.get('debit_note_tax')]
            for tag in tag_list:
                if tag:
                    move_lines = self._get_account_move_lines_by_tag(tag[0])
                    for move_line in move_lines:
                        # move_line = self.env['account.move.line'].browse(tax_detail.get('base_line_id'))
                        # if move_line:
                        data.append({
                            'Serial #': serial_no,
                            'Tax Payer TRN': self.env.company.vat or '',
                            'Company Name / Member Company Name (If applicable)': self.env.company.name,
                            'Tax Invoice/Tax credit note  No': move_line.move_id.name,
                            'Tax Invoice/Tax credit note Date - DD/MM/YYYY format only': move_line.move_id.invoice_date.strftime("%d/%m/%Y") if move_line.move_id.invoice_date else '',
                            'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)': '{} to {}'.format(self.from_date.strftime("%d/%m/%Y"), self.to_date.strftime("%d/%m/%Y")),
                            'Tax Invoice/Tax credit note Amount AED': move_line.credit,
                            'Customer Name': move_line.move_id.partner_id.name,
                            'Customer TRN (If applicable)': move_line.move_id.partner_id.vat or '',
                            'Location of the Customer': "{}, {}".format(move_line.move_id.partner_id.state_id.name or '', move_line.move_id.partner_id.country_id.name),
                            'Clear description of the supply': move_line.name,
                        })
        return data

    def worksheet_box4(self, workbook):
        worksheet = workbook.add_worksheet("Zero Rated Sales - Box 4")
        header_list = ['Serial #', 'Tax Payer TRN', 'Company Name / Member Company Name (If applicable)', 'Tax Invoice/Tax credit note  No',
                       'Tax Invoice/Tax credit note Date - DD/MM/YYYY format only', 'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)', 'Tax Invoice/Tax credit note Amount AED',
                       'Customer Name', 'Customer TRN (If applicable)', 'Location of the Customer', 'Clear description of the supply']
        self.set_header_row(workbook, worksheet, header_list)
        worksheet_data = self.worksheet_box4_data()
        content_row = 1
        for data in worksheet_data:
            for col, value in data.items():
                column_index = header_list.index(col)
                worksheet.write(content_row, column_index, value)
            content_row += 1

    def worksheet_box5_data(self):
        sale_tax_data_list, purchase_tax_data_list = self._prepare_tax_data_list()
        box1_serial_nos = ['5']
        data = []
        AccountMoveLine = self.env['account.move.line']
        for serial_no in box1_serial_nos:
            sale_tax_data = list(filter(lambda item: item.get('box') == serial_no, sale_tax_data_list))
            sale_tax_data = sale_tax_data and sale_tax_data[0]
            tag_list = [sale_tax_data.get('amount_tag_name'), sale_tax_data.get('amount_vat_tag_name'), sale_tax_data.get('credit_vat_base'), sale_tax_data.get('debit_note_tax')]
            for tag in tag_list:
                if tag:
                    AccountMoveLine |= self._get_account_move_lines_by_tag(tag[0])
            for move_line in AccountMoveLine:
                sign = 1 if move_line.move_id.move_type in ['out_invoice', 'in_invoice'] else -1
                data.append({
                    'Serial #': serial_no,
                    'Tax Payer TRN': self.env.company.vat or '',
                    'Company Name / Member Company Name (If applicable)': self.env.company.name,
                    'Tax Invoice/Tax credit note  No': move_line.move_id.name,
                    'Tax Invoice/Tax credit note Date - DD/MM/YYYY format only': move_line.move_id.invoice_date.strftime("%d/%m/%Y") if move_line.move_id.invoice_date else '',
                    'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)': '{} to {}'.format(self.from_date.strftime("%d/%m/%Y"), self.to_date.strftime("%d/%m/%Y")),
                    'Tax Invoice/Tax credit note Amount AED': move_line.price_subtotal * sign,
                    'Customer Name': move_line.move_id.partner_id.name,
                    'Customer TRN': move_line.move_id.partner_id.vat or '',
                    'Clear description of the supply': move_line.name,
                })
        return data

    def worksheet_box5(self, workbook):
        worksheet = workbook.add_worksheet("Exempt Supplies - Box 5")
        header_list = ['Serial #', 'Tax Payer TRN', 'Company Name / Member Company Name (If applicable)', 'Tax Invoice/Tax credit note  No',
                       'Tax Invoice/Tax credit note Date - DD/MM/YYYY format only', 'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)', 'Tax Invoice/Tax credit note Amount AED',
                       'Customer Name', 'Customer TRN', 'Clear description of the supply']
        self.set_header_row(workbook, worksheet, header_list)
        worksheet_data = self.worksheet_box5_data()
        content_row = 1
        for data in worksheet_data:
            for col, value in data.items():
                column_index = header_list.index(col)
                worksheet.write(content_row, column_index, value)
            content_row += 1

    def worksheet_box6_data(self):
        sale_tax_data_list, purchase_tax_data_list = self._prepare_tax_data_list()
        box1_serial_nos = ['6']
        data = []
        # AccountMoveLine = self.env['account.move.line']
        for serial_no in box1_serial_nos:
            sale_tax_data = list(filter(lambda item: item.get('box') == serial_no, sale_tax_data_list))
            sale_tax_data = sale_tax_data and sale_tax_data[0]
            tag_list = [sale_tax_data.get('amount_vat_tag_name'), sale_tax_data.get('debit_note_tax')]
            for tag in tag_list:
                if tag:
                    move_lines = self._get_account_move_lines_by_tag(tag[0])
                    for move_line in move_lines:
                        sign = 1 if move_line.move_id.move_type in ['out_invoice', 'in_invoice'] else -1
                        data.append({
                            'Serial #': serial_no,
                            'Tax Payer TRN': self.env.company.vat or '',
                            'Company Name / Member Company Name (If applicable)': self.env.company.name,
                            'Tax Invoice/Tax credit note No': move_line.move_id.name,
                            'Invoice/ credit note Date - DD/MM/YYYY format only': move_line.move_id.invoice_date.strftime("%d/%m/%Y") if move_line.move_id.invoice_date else '',
                            'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)': '{} to {}'.format(self.from_date.strftime("%d/%m/%Y"), self.to_date.strftime("%d/%m/%Y")),
                            'Invoice/credit note Amount AED (before VAT)': move_line.move_id.amount_untaxed * sign,
                            'VAT Amount AED': move_line.balance,
                            'Supplier Name': move_line.move_id.partner_id.name,
                            'Location of the Supplier': "{}, {}".format(move_line.move_id.partner_id.state_id.name or '', move_line.move_id.partner_id.country_id.name),
                            'Name of the Customs Authority': '',
                            'Customs Declaration Number': '',
                            'Clear description of the transaction': move_line.name,
                        })
        return data

    def worksheet_box6(self, workbook):
        worksheet = workbook.add_worksheet("Goods Imported into UAE -Box6")
        header_list = ['Serial #', 'Tax Payer TRN', 'Company Name / Member Company Name (If applicable)', 'Tax Invoice/Tax credit note No', 'Invoice/ credit note Date - DD/MM/YYYY format only',
                       'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)', 'Invoice/credit note Amount AED (before VAT)', 'VAT Amount AED', 'Supplier Name', 'Location of the Supplier',
                       'Name of the Customs Authority', 'Customs Declaration Number', 'Clear description of the transaction']
        self.set_header_row(workbook, worksheet, header_list)
        worksheet_data = self.worksheet_box6_data()
        content_row = 1
        for data in worksheet_data:
            for col, value in data.items():
                column_index = header_list.index(col)
                worksheet.write(content_row, column_index, value)
            content_row += 1

    def worksheet_box7(self, workbook):
        worksheet = workbook.add_worksheet("Adjustment - Goods Import -Box7")
        header_list = ['Serial #', 'Tax Payer TRN', 'Company Name / Member Company Name (If applicable)', 'Tax Invoice/Tax credit note No', 'Invoice/ credit note Date - DD/MM/YYYY format only',
                       'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)', 'Invoice/credit note Amount AED (before VAT) ', 'VAT Amount AED ', 'Supplier Name', 'Location of the Supplier',
                       'Name of the Customs Authority', 'Customs Declaration Number', 'Reason for the adjustment']
        self.set_header_row(workbook, worksheet, header_list)

    def worksheet_box9_data(self):
        sale_tax_data_list, purchase_tax_data_list = self._prepare_tax_data_list()
        box1_serial_nos = ['9']
        data = []
        for serial_no in box1_serial_nos:
            purchase_tax_data = list(filter(lambda item: item.get('box') == serial_no, purchase_tax_data_list))
            purchase_tax_data = purchase_tax_data and purchase_tax_data[0]
            # AccountMoveLine = self.env['account.move.line']
            tag_list = [purchase_tax_data.get('amount_vat_tag_name'), purchase_tax_data.get('debit_note_tax')]
            if purchase_tax_data:

                for tag in tag_list:
                    if tag:
                        move_lines = self._get_account_move_lines_by_tag(tag[0])
                        for move_line in move_lines:
                            sign = 1 if move_line.move_id.move_type in ['out_invoice', 'in_invoice'] else -1
                            data.append({
                                'Serial #': serial_no,
                                'Tax Payer TRN': self.env.company.vat or '',
                                'Company Name / Member Company Name (If applicable)': self.env.company.name,
                                'Tax Invoice/Tax credit note  No': move_line.move_id.name,
                                'Tax Invoice/Tax credit note Date - DD/MM/YYYY format only': move_line.move_id.invoice_date.strftime("%d/%m/%Y") if move_line.move_id.invoice_date else '',
                                'Tax Invoice/Tax credit note Received Date - DD/MM/YYYY format only': move_line.move_id.date.strftime("%d/%m/%Y") if move_line.move_id.date else '',
                                'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)': '{} to {}'.format(self.from_date.strftime("%d/%m/%Y"), self.to_date.strftime("%d/%m/%Y")),
                                'Tax Invoice/Tax credit note Amount AED (before VAT)': move_line.move_id.amount_untaxed * sign,
                                'VAT Amount AED': move_line.balance,
                                'VAT Amount Recovered AED': '',
                                'Supplier  Name': move_line.move_id.partner_id.name,
                                'Supplier  TRN': move_line.move_id.partner_id.vat or '',
                                'Clear description of the supply': move_line.name,
                                'VAT Adjustments (if any)': ''
                            })
        return data

    def worksheet_box9(self, workbook):
        worksheet = workbook.add_worksheet("Std Rated Purchases - Box 9")
        header_list = ['Serial #', 'Tax Payer TRN', 'Company Name / Member Company Name (If applicable)', 'Tax Invoice/Tax credit note  No',
                       'Tax Invoice/Tax credit note Date - DD/MM/YYYY format only', 'Tax Invoice/Tax credit note Received Date - DD/MM/YYYY format only',
                       'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)', 'Tax Invoice/Tax credit note Amount AED (before VAT)', 'VAT Amount AED', 'VAT Amount Recovered AED',
                       'Supplier  Name', 'Supplier  TRN', 'Clear description of the supply', 'VAT Adjustments (if any)']
        self.set_header_row(workbook, worksheet, header_list)
        worksheet_data = self.worksheet_box9_data()
        content_row = 1
        for data in worksheet_data:
            for col, value in data.items():
                column_index = header_list.index(col)
                worksheet.write(content_row, column_index, value)
            content_row += 1

    def worksheet_box10_data(self):
        sale_tax_data_list, purchase_tax_data_list = self._prepare_tax_data_list()
        box1_serial_nos = ['10']
        data = []
        for serial_no in box1_serial_nos:
            purchase_tax_data = list(filter(lambda item: item.get('box') == serial_no, purchase_tax_data_list))
            purchase_tax_data = purchase_tax_data and purchase_tax_data[0]
            AccountMoveLine = self.env['account.move.line']
            if purchase_tax_data:
                tag_list = [purchase_tax_data.get('amount_vat_tag_name'), purchase_tax_data.get('debit_note_tax')]
                for tag in tag_list:
                    if tag:
                        AccountMoveLine |= self._get_account_move_lines_by_tag(tag[0])
                for move_line in AccountMoveLine:
                    sign = 1 if move_line.move_id.move_type in ['out_invoice', 'in_invoice'] else -1
                    data.append({
                        'Serial #': serial_no,
                        'Tax Payer TRN': self.env.company.vat or '',
                        'Company Name / Member Company Name (If applicable)': self.env.company.name,
                        'Tax Invoice/Tax credit note No': move_line.move_id.name,
                        'Invoice/ credit note Date - DD/MM/YYYY format only': move_line.move_id.invoice_date.strftime("%d/%m/%Y") if move_line.move_id.invoice_date else '',
                        'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)': '{} to {}'.format(self.from_date.strftime("%d/%m/%Y"), self.to_date.strftime("%d/%m/%Y")),
                        'Invoice/credit note Amount AED (before VAT)': move_line.move_id.amount_untaxed * sign,
                        'VAT Amount AED': move_line.balance,
                        'Supplier Name': move_line.move_id.partner_id.name,
                        'Location of the Supplier': "{}, {}".format(move_line.move_id.partner_id.state_id.name or '', move_line.move_id.partner_id.country_id.name),
                        'Clear description of the transaction': move_line.name,
                    })
        return data

    def worksheet_box10(self, workbook):
        worksheet = workbook.add_worksheet("Supplies subject to RCM - Box10")
        header_list = ['Serial #', 'Tax Payer TRN', 'Company Name / Member Company Name (If applicable)', 'Tax Invoice/Tax credit note No', 'Invoice/ credit note Date - DD/MM/YYYY format only',
                       'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)', 'Invoice/credit note Amount AED (before VAT)', 'VAT Amount AED', 'Supplier Name', 'Location of the Supplier',
                       'Clear description of the transaction']
        self.set_header_row(workbook, worksheet, header_list)
        worksheet_data = self.worksheet_box10_data()
        content_row = 1
        for data in worksheet_data:
            for col, value in data.items():
                column_index = header_list.index(col)
                worksheet.write(content_row, column_index, value)
            content_row += 1

    def action_print_excel(self):
        self.ensure_one()
        self.with_context(keep_amount=True).fetch_tax_information()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        self.worksheet_box1(workbook)
        self.worksheet_out_of_scope_sales(workbook)
        self.worksheet_box2(workbook)
        self.worksheet_box3(workbook)
        self.worksheet_box4(workbook)
        self.worksheet_box5(workbook)
        self.worksheet_box6(workbook)
        self.worksheet_box7(workbook)
        self.worksheet_box9(workbook)
        self.worksheet_box10(workbook)
        workbook.close()
        content = output.getvalue()
        filename = '{}.xlsx'.format(self.display_name)
        AttachmentObj = self.env['ir.attachment']
        attachment = AttachmentObj.search([('name', '=', filename), ('res_id', '=', self.id)], limit=1)
        if not attachment:
            attachment = AttachmentObj.create({
                'name': filename,
                'datas': base64.b64encode(content),
                'store_fname': filename,
                'res_model': self._name,
                'res_id': self.id,
                'type': 'binary',
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            })
        else:
            attachment.write({'datas': base64.b64encode(content)})
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas&download=true&filename=%s' % (attachment.id, filename),
            'target': 'new',
        }
