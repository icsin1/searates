# -*- coding: utf-8 -*-

import io
import base64
import xlsxwriter
from odoo import models, fields, _
from odoo.exceptions import UserError


class OpportunityDetailReport(models.TransientModel):
    _name = 'opportunity.detail.report'
    _description = 'Opportunity Detail Report'

    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    stage_ids = fields.Many2many("crm.prospect.opportunity.stage", string="Opportunity Status")
    company_ids = fields.Many2many('res.company', string='Company')

    def print_xlsx(self):
        attachment = self.sudo().download_xlsx_report()
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas&download=true&filename=%s' % (attachment.id, attachment.name),
            'target': 'new',
        }

    def download_xlsx_report(self):
        if self.to_date < self.from_date:
            raise UserError(_("To Date must be greater than From Date."))
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)

        heading_style_1 = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '20px'})
        heading_style_2 = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '11px'})
        line_style_1 = workbook.add_format({'align': 'center', 'bold': True})
        line_style_2 = workbook.add_format({'align': 'center'})
        worksheet = workbook.add_worksheet('Opportunity Detail Report')

        from_date = self.from_date.strftime('%d %b %Y')
        to_date = self.to_date.strftime('%d %b %Y')

        companies = self.company_ids and ', '.join(self.company_ids.mapped('name')) or ''
        status = self.stage_ids and ', '.join(self.stage_ids.mapped('name')) or ''
        worksheet.write(0, 0, 'Company', heading_style_2)
        worksheet.merge_range(0, 1, 0, 3, companies, line_style_2)
        worksheet.write(1, 0, 'Opportunity Status', heading_style_2)
        worksheet.merge_range(1, 1, 1, 3, status, line_style_2)

        worksheet.merge_range(2, 0, 3, 29, 'Opportunity Details Report', heading_style_1)
        worksheet.merge_range(4, 0, 4, 29, from_date + ' - ' + to_date, heading_style_2)
        worksheet.set_column(0, 29, 18)
        row = 5
        col = 0
        header_lines = ['Company', 'Opportunity Number', 'Opportunity Date', 'Opportunity Status', 'Lead No', 'Lead Date',
                        'Transport Mode', 'Shipment Type', 'Cargo Type', 'Inco Terms', 'Service Mode', 'Commodity', 'Opportunity Source',
                        'Opportunity Type', 'Type (Shipment/Service Jobs)', 'Sales Team', 'Sales Agent', 'Pricing Team', 'Cargo Status',
                        'Origin Country', 'Destination Country', 'Customer', 'Shipper/Consignee', 'Quotation No', 'Shipment Date', 'Shipment Number',
                        'Shipment / Service Job', 'Opp. To Quot Conv Days', 'Opp. To Quot Conv Hrs', 'Opp. To Quot Conv Min']

        for header_line in header_lines:
            worksheet.write(row, col, header_line, line_style_1)
            col = (col+1)
        row = 6

        domain = [('date', '>=', self.from_date), ('date', '<=', self.to_date)]
        if self.stage_ids:
            domain.append(('stage_id', 'in', self.stage_ids.ids))
        if self.company_ids:
            domain.append(('company_id', 'in', self.company_ids.ids))
        opportunity_ids = self.env['crm.prospect.opportunity'].search(domain)

        for opportunity in opportunity_ids:
            worksheet_list = []
            if not opportunity.quotation_ids:
                self.opportunity_data(worksheet_list=worksheet_list, opportunity=opportunity)
                worksheet_list.append('')
                worksheet_list.append('')
                worksheet_list.append('')
                worksheet_list.append('')

                opp_to_quote_convert_days = ''
                opp_to_quote_convert_hours = ''
                opp_to_quote_convert_minutes = ''
                worksheet_list.append(opp_to_quote_convert_days)
                worksheet_list.append(opp_to_quote_convert_hours)
                worksheet_list.append(opp_to_quote_convert_minutes)

                col = 0
                for sheet_data in worksheet_list:
                    worksheet.write(row, col, sheet_data, line_style_2)
                    col = col + 1
                if worksheet_list:
                    row = row + 1
            else:
                for quote in opportunity.quotation_ids:
                    worksheet_list = []
                    if not quote.freight_shipment_ids:
                        self.opportunity_data(worksheet_list=worksheet_list, opportunity=opportunity)
                        worksheet_list.append(quote.name or '')
                        worksheet_list.append('')
                        worksheet_list.append('')
                        worksheet_list.append(dict(quote._fields['quote_for'].selection).get(quote.quote_for))
                        time_difference = quote.create_date - opportunity.create_date
                        opp_to_quote_convert_days = time_difference.days
                        opp_to_quote_convert_hours = time_difference.seconds // 3600
                        opp_to_quote_convert_minutes = (time_difference.seconds % 3600) // 60
                        worksheet_list.append(opp_to_quote_convert_days)
                        worksheet_list.append(opp_to_quote_convert_hours)
                        worksheet_list.append(opp_to_quote_convert_minutes)
                    else:
                        for shipment in quote.freight_shipment_ids:
                            self.opportunity_data(worksheet_list=worksheet_list, opportunity=opportunity)
                            worksheet_list.append(quote.name or '')
                            worksheet_list.append(shipment.shipment_date and shipment.shipment_date.strftime("%Y-%m-%d") or '')
                            worksheet_list.append(shipment.name or '')
                            worksheet_list.append(dict(quote._fields['quote_for'].selection).get(quote.quote_for))
                            time_difference = quote.create_date - opportunity.create_date
                            opp_to_quote_convert_days = time_difference.days
                            opp_to_quote_convert_hours = time_difference.seconds // 3600
                            opp_to_quote_convert_minutes = (time_difference.seconds % 3600) // 60
                            worksheet_list.append(opp_to_quote_convert_days)
                            worksheet_list.append(opp_to_quote_convert_hours)
                            worksheet_list.append(opp_to_quote_convert_minutes)
                    col = 0
                    for sheet_data in worksheet_list:
                        worksheet.write(row, col, sheet_data, line_style_2)
                        col = col + 1
                    if worksheet_list:
                        row = row + 1
        workbook.close()
        filename = 'Opportunity Detail Report %s-%s' % (self.from_date.strftime('%d%b%Y'), self.to_date.strftime('%d%b%Y'))
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
        return attachment

    def opportunity_data(self, worksheet_list, opportunity):
        worksheet_list.append(opportunity.company_id and opportunity.company_id.name or '')
        worksheet_list.append(opportunity.name or '')
        worksheet_list.append(opportunity.date and opportunity.date.strftime("%Y-%m-%d") or '')
        worksheet_list.append(opportunity.stage_id.name or '')
        worksheet_list.append(opportunity.lead_id and opportunity.lead_id.name or '')
        worksheet_list.append(opportunity.lead_id and opportunity.lead_id.date and opportunity.lead_id.date.strftime("%Y-%m-%d") or '')
        worksheet_list.append(opportunity.transport_mode_id and opportunity.transport_mode_id.name or '')
        worksheet_list.append(opportunity.shipment_type_id and opportunity.shipment_type_id.name or '')
        worksheet_list.append(opportunity.cargo_type_id and opportunity.cargo_type_id.name or '')
        worksheet_list.append(opportunity.incoterm_id and opportunity.incoterm_id.name or '')
        worksheet_list.append(opportunity.service_mode_id and opportunity.service_mode_id.name or '')
        worksheet_list.append(opportunity.commodity_id and opportunity.commodity_id.name or '')
        worksheet_list.append(dict(opportunity._fields['opportunity_source'].selection).get(opportunity.opportunity_source))
        worksheet_list.append(dict(opportunity._fields['opportunity_type'].selection).get(opportunity.opportunity_type))
        worksheet_list.append(dict(opportunity._fields['opportunity_for'].selection).get(opportunity.opportunity_for))
        worksheet_list.append(opportunity.team_id and opportunity.team_id.name or '')
        worksheet_list.append(opportunity.user_id and opportunity.user_id.name or '')
        worksheet_list.append(opportunity.pricing_team_id and opportunity.pricing_team_id.name or '')
        worksheet_list.append(dict(opportunity._fields['cargo_status'].selection).get(opportunity.cargo_status))
        worksheet_list.append(opportunity.origin_country_id and opportunity.origin_country_id.name or '')
        worksheet_list.append(opportunity.destination_country_id and opportunity.destination_country_id.name or '')
        worksheet_list.append(opportunity.prospect_id and opportunity.prospect_id.name or '')
        worksheet_list.append(dict(opportunity._fields['customer_type'].selection).get(opportunity.customer_type))
        return worksheet_list

    def send_by_email(self):
        template_id = self.env['ir.model.data']._xmlid_to_res_id('fm_quote_reports.opportunity_report_email_template', raise_if_not_found=False)
        attachment = self.sudo().download_xlsx_report()
        ctx = {
            'default_model': self._name,
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'custom_layout': "mail.mail_notification_light",
            'default_attachment_ids': attachment.ids,
            'subject': 'Opportunity Detail Report',
        }
        return {
            'name': 'Report Send by Email: Opportunity Detail Report',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
