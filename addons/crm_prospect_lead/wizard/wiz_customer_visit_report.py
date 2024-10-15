from odoo import models, fields, api, _
import base64
import io
import xlsxwriter
from odoo.exceptions import ValidationError


class CustomerVisitReport(models.TransientModel):
    _name = "customer.visit.report"

    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    sales_agent_ids = fields.Many2many('res.users', string='Sales Agent')
    customer_ids = fields.Many2many('res.partner', string='Customer')

    @api.constrains('from_date', 'to_date')
    def _check_from_date_to_date(self):
        for rec in self:
            if rec.to_date < rec.from_date:
                raise ValidationError(_('To date should not be smaller than the From date.'))

    def print_report_pdf(self):
        data = {
            'model_id': self.id,
            'from_date': self.from_date,
            'to_date': self.to_date,
            'sales_agent_ids': self.sales_agent_ids.ids,
            'customer_ids': self.customer_ids.ids,
        }
        return self.env.ref('crm_prospect_lead.action_report_customer_visit').report_action(self, data=data)

    def print_report_xlsx(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        header = workbook.add_format({'align': 'center', 'bold': True})
        style_1 = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '10px', 'bg_color': '#b1b1b1', 'border': 1})
        style_2 = workbook.add_format({'align': 'center', 'font_size': '10px'})
        col = 14
        worksheet = workbook.add_worksheet('Customer Visit Report')
        worksheet.merge_range(0, 0, 1, 14, 'Customer Visit Report', header)
        worksheet.set_column(0, col, 15)
        worksheet.write(2, 0, 'Total Visit', style_1)
        worksheet.write(2, 1, 'Customer Name', style_1)
        worksheet.write(2, 2, 'Company Name', style_1)
        worksheet.write(2, 3, 'Company Address', style_1)
        worksheet.write(2, 4, 'Contact Person', style_1)
        worksheet.write(2, 5, 'Designation', style_1)
        worksheet.write(2, 6, 'Contact Number', style_1)
        worksheet.write(2, 7, 'Email', style_1)
        worksheet.write(2, 8, 'Customer Visit Date', style_1)
        worksheet.write(2, 9, 'Customer Visit Time', style_1)
        worksheet.write(2, 10, 'Communication Mode', style_1)
        worksheet.write(2, 11, 'Visitor Name', style_1)
        worksheet.write(2, 12, 'Next Visit Scheduled', style_1)
        worksheet.write(2, 13, 'Next Follow Up Date', style_1)
        worksheet.write(2, 14, 'Assigned Person', style_1)
        row = 3
        col = 0

        domain = [('date_of_visit', '>=', self.from_date),
                  ('date_of_visit', '<=', self.to_date),
                  ('visited_by_id', 'in', self.sales_agent_ids.ids),
                  ('customer_id', 'in', self.customer_ids.ids)
                  ]
        visit_line_ids = self.env['customer.visit.lines'].sudo().search(domain)
        date_format = '%m/%d/%Y'
        if visit_line_ids:
            for line in visit_line_ids:
                serial = line.serial_no
                customer_name = line.customer_id.name
                company = line.company_id.name
                address = ' '.join((line.opportunity_id.street1,
                                    line.opportunity_id.street2 if line.opportunity_id.street2 else '',
                                    line.opportunity_id.city_id.name if line.opportunity_id.city_id else '',
                                    line.opportunity_id.state_id.name if line.opportunity_id.state_id else '',
                                    line.opportunity_id.country_id.name,
                                    line.opportunity_id.zip if line.opportunity_id.zip else ''
                                    ))
                contact_name = line.opportunity_id.contact_name if line.opportunity_id.contact_name else ''
                designation = line.opportunity_id.designation if line.opportunity_id.designation else ''
                mobile = line.opportunity_id.mobile if line.opportunity_id.mobile else ''
                email = line.opportunity_id.email if line.opportunity_id.email else ''
                date_of_visit = line.date_of_visit.strftime(date_format)
                time_of_visit = line.time_of_visit
                opportunity_source = line.opportunity_id.opportunity_source if line.opportunity_id.opportunity_source else ''
                visitor_name = line.opportunity_id.user_id.name
                next_visit = dict(line._fields['next_visit'].selection).get(line.next_visit)
                next_followup = line.next_followup_date.strftime(date_format) if line.next_followup_date else ''
                assigned_person = line.assign_to_id.name

                worksheet.write(row, col,  serial, style_2)
                worksheet.write(row, col + 1, customer_name, style_2)
                worksheet.write(row, col + 2, company, style_2)
                worksheet.write(row, col + 3, address, style_2)
                worksheet.write(row, col + 4, contact_name, style_2)
                worksheet.write(row, col + 5, designation, style_2)
                worksheet.write(row, col + 6, mobile, style_2)
                worksheet.write(row, col + 7, email, style_2)
                worksheet.write(row, col + 8, date_of_visit, style_2)
                worksheet.write(row, col + 9, time_of_visit, style_2)
                worksheet.write(row, col + 10, opportunity_source, style_2)
                worksheet.write(row, col + 11, visitor_name, style_2)
                worksheet.write(row, col + 12, next_visit, style_2)
                worksheet.write(row, col + 13, next_followup, style_2)
                worksheet.write(row, col + 14, assigned_person, style_2)
                col = 0
                row += 1
        workbook.close()
        filename = 'Customer Visit Report %s-%s' % (self.from_date.strftime('%d%b%Y'), self.to_date.strftime('%d%b%Y'))
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
            'target': 'new',
        }
