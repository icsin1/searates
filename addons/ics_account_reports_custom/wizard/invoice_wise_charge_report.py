# -*- coding: utf-8 -*-

import io
import base64
import xlsxwriter
from odoo import models, fields, _
from odoo.exceptions import UserError
import csv


class InvoiceChargeReport(models.TransientModel):
    _name = 'invoice.charge.report'
    _description = 'Invoice Charge Wise Report'

    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    charge_ids = fields.Many2many('product.product', string='Charges')
    company_ids = fields.Many2many('res.company', string='Company')

    def print_csv(self):
        attachment = self.sudo().download_csv_report()
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas&download=true&filename=%s' % (attachment.id, attachment.name),
            'target': 'new',
        }

    def print_xlsx(self):
        attachment = self.sudo().download_xlsx_report()
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas&download=true&filename=%s' % (attachment.id, attachment.name),
            'target': 'new',
        }

    def worksheet_data(self):
        domain = [('move_id.invoice_date', '>=', self.from_date), ('move_id.invoice_date', '<=', self.to_date),
                  ('move_id.move_type', '=', 'out_invoice'), ('exclude_from_invoice_tab', '=', False),('product_id','!=',False)]
        if self.charge_ids:
            domain.append(('product_id', 'in', self.charge_ids.ids))
        if self.company_ids:
            domain.append(('move_id.company_id', 'in', self.company_ids.ids))
        invoice_line_ids = self.env['account.move.line'].search(domain)
        data = []
        for line in invoice_line_ids:
            invoice = line.move_id
            if line.house_shipment_id:
                job_no = line.house_shipment_id.name
                job_type = 'Shipment'
            elif line.service_job_id:
                job_no = line.service_job_id.name
                job_type = 'Service Job'
            else:
                job_no = ''
                job_type = ''
            if 'x_zajel_ref_no' in self.env['res.partner']._fields:
                customer_code = invoice.partner_id.x_zajel_ref_no
            else:
                customer_code = invoice.partner_id.customer_code
            roe = line.price_subtotal/line.credit if line.credit > 0 else line.price_subtotal
            data.append({
                'Company Name': invoice.company_id.name or '',
                'Invoice No': invoice.name or '',
                'Invoice Date': invoice.invoice_date.strftime("%d/%m/%Y") if invoice.invoice_date else '',
                'Customer Code': customer_code or '',
                'Customer Name': invoice.partner_id.name or '',
                'Shipment/Service Job No': job_no,
                'Shipment/Service Job': job_type,
                'Charge Name': line.product_id.name,
                'Currency': invoice.currency_id.name,
                'Currency Amount': line.credit,
                'ROE': roe,
                'Local Amount': line.price_subtotal,
                'Tax Amount': line.l10n_ae_vat_amount,
                'Total Amount': line.price_total
            })
        return data

    def download_csv_report(self):
        if self.to_date < self.from_date:
            raise UserError(_("To Date must be greater than From Date."))
        output = io.StringIO()
        header_list = ['Company Name', 'Invoice No', 'Invoice Date', 'Customer Code', 'Customer Name', 'Shipment/Service Job No',
                       'Shipment/Service Job', 'Charge Name', 'Currency', 'Currency Amount', 'ROE', 'Local Amount',
                       'Tax Amount', 'Total Amount']
        writer = csv.DictWriter(output, fieldnames=header_list, delimiter='\t')
        csv_data = self.worksheet_data()
        writer.writeheader()
        writer.writerows(csv_data)
        first_name_user = self.env.user.name.split(' ')
        filename = '%s%s%s.csv' % (first_name_user[0], self.from_date.strftime('%d%m%y'), self.to_date.strftime('%d%m%y'))
        content = output.getvalue().encode()
        attachment_obj = self.env['ir.attachment']
        attachment = attachment_obj.search([('name', '=', filename)], limit=1)
        if not attachment:
            attachment = attachment_obj.create({
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
        return attachment

    def download_xlsx_report(self):
        if self.to_date < self.from_date:
            raise UserError(_("To Date must be greater than From Date."))
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Invoice Charge Wise Report')
        line_style_1 = workbook.add_format({'align': 'center', 'bold': True})
        line_style_2 = workbook.add_format({'align': 'center'})
        row = 0
        header_list = ['Company Name', 'Invoice No', 'Invoice Date', 'Customer Code', 'Customer Name', 'Shipment/Service Job No',
                       'Shipment/Service Job', 'Charge Name', 'Currency', 'Currency Amount', 'ROE', 'Local Amount',
                       'Tax Amount', 'Total Amount']
        for col, header in enumerate(header_list):
            worksheet.write(row, col, header, line_style_1)
        row = 1
        worksheet_data = self.worksheet_data()
        for data in worksheet_data:
            for col, value in data.items():
                column_index = header_list.index(col)
                worksheet.write(row, column_index, value, line_style_2)
            row += 1
        worksheet.autofit()
        workbook.close()
        first_name_user = self.env.user.name.split(' ')
        filename = '%s%s%s' % (first_name_user[0], self.from_date.strftime('%d%m%y'), self.to_date.strftime('%d%m%y'))
        content = output.getvalue()
        attachment_obj = self.env['ir.attachment']
        attachment = attachment_obj.search([('name', '=', filename)], limit=1)
        if not attachment:
            attachment = attachment_obj.create({
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
        return attachment
