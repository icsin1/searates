# -*- coding: utf-8 -*-

import base64
import io
import xlsxwriter
from odoo import models, fields
from odoo.tools.misc import format_date


class WizardCustomerDueReport(models.TransientModel):
    _name = 'wizard.customer.due.report'
    _description = 'Customer Due Report'

    to_date = fields.Date(string='To Date', required=True)
    customer_ids = fields.Many2many('res.partner', string='Customer')
    user_ids = fields.Many2many('res.users', string='Salesman')
    invoice_date_for = fields.Selection([('invoice_date', 'Invoice Date'), ('due_date', 'Due Date')], default='invoice_date', string='Invoice/Due Dates')
    due_status = fields.Selection([('overdue', 'Overdue'), ('non_overdue', 'Non Overdue')], default='overdue', string='Status')
    company_id = fields.Many2one('res.company', required=True, string='Company', default=lambda self: self.env.company.id)

    def print_xlsx_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        style_1 = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '10px'})
        style_2 = workbook.add_format({'align': 'center', 'font_size': '10px'})
        worksheet = workbook.add_worksheet('Customer Due Report')
        worksheet.set_column(0, 18, 20)
        header_list = ['Invoice No', 'Invoice Date', 'Party Name', 'Invoice Amount', 'OS Amount', 'No.of Days', 'Due Date', 'Credit Terms', 'Status', 'Invoice Sales Person', 'Customer Sales Person']
        col = 0
        row = 0
        for header in header_list:
            worksheet.write(row, col, header, style_1)
            col += 1

        invoice_list_data = self.get_customer_invoice_data()
        row = 1
        col = 0
        for invoice_data in invoice_list_data:
            worksheet.write(row, col, invoice_data['invoice_no'], style_2)
            worksheet.write(row, col + 1, invoice_data['invoice_date'], style_2)
            worksheet.write(row, col + 2, invoice_data['partner_name'], style_2)
            worksheet.write(row, col + 3, invoice_data['amount_total_signed'], style_2)
            worksheet.write(row, col + 4, invoice_data['amount_residual_signed'], style_2)
            worksheet.write(row, col + 5, invoice_data['no_of_days_total'], style_2)
            worksheet.write(row, col + 6, invoice_data['invoice_date_due'], style_2)
            worksheet.write(row, col + 7, invoice_data['credit_terms'], style_2)
            worksheet.write(row, col + 8, invoice_data['inv_status'], style_2)
            worksheet.write(row, col + 9, invoice_data['user_name'], style_2)
            worksheet.write(row, col + 10, invoice_data['sales_person_name'], style_2)
            col = 0
            row += 1

        workbook.close()
        filename = 'Customer Due Report %s' % (self.to_date.strftime('%d%b%Y'))
        content = output.getvalue()
        AttachmentObj = self.env['ir.attachment']
        attachment = AttachmentObj.search([('name', '=', filename)], limit=1)
        if not attachment:
            attachment = AttachmentObj.create({
                'name': filename,
                'datas': base64.b64encode(content),
                'store_fname': filename,
                'res_model': self._name,
                'res_id': 0,
                'type': 'binary',
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            })
        else:
            attachment.write({'datas': base64.b64encode(content)})
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas&download=true&filename=%s' % (attachment.id, filename),
            'target': 'new'
        }

    def get_customer_invoice_data(self, partner_id=False):
        invoice_data = []
        account_move_domain = [('invoice_date', '<=', self.to_date), ('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('company_id', '=', self.company_id.id),
                               ('payment_state', 'in', ['not_paid', 'partial'])]
        if self.customer_ids and not partner_id:
            account_move_domain.append(('partner_id', 'in', self.customer_ids.ids))
        if partner_id:
            account_move_domain.append(('partner_id', '=', partner_id.id))
        if self.user_ids:
            account_move_domain.append(('invoice_user_id', 'in', self.user_ids.ids))

        customer_inv_ids = self.env['account.move'].search(account_move_domain)
        payment_term_days = 0
        no_of_days_total = 0
        inv_status = ''
        for inv in customer_inv_ids:
            payment_term_days = inv.partner_id.property_payment_term_id.line_ids.filtered(lambda term_line: term_line.value == 'balance').days
            if self.invoice_date_for:
                if inv.invoice_date:
                    no_of_days_total = abs(self.to_date - inv.invoice_date).days
                if inv.invoice_date_due:
                    no_of_days_total = abs(self.to_date - inv.invoice_date_due).days

            credit_terms = payment_term_days or 0
            if credit_terms < no_of_days_total and self.due_status == 'overdue':
                inv_status = 'Overdue'
            elif credit_terms == no_of_days_total and self.due_status == 'non_overdue':
                inv_status = 'Non Overdue'
            else:
                inv_status = 'Non Overdue'

            vals = {'invoice_no': inv.name, 'invoice_date': format_date(self.env, inv.invoice_date), 'partner_name': inv.partner_id.name,
                    'amount_total_signed': inv.amount_total_signed, 'amount_residual_signed': inv.amount_residual_signed,
                    'no_of_days_total': no_of_days_total, 'credit_terms': credit_terms, 'invoice_date_due': format_date(self.env, inv.invoice_date_due),
                    'inv_status': inv_status, 'user_name': inv.invoice_user_id.name or '', 'sales_person_name': inv.partner_id.user_id.name or ''
                    }
            invoice_data.append(vals)
        return invoice_data
