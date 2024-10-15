# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons.fm_quote.models.shipment_quote import STATES
import base64
import io
import xlsxwriter
from odoo.tools.misc import get_lang


class WizSalesAgentReport(models.TransientModel):
    _name = 'wiz.sales.agent.report'
    _description = 'Wiz Sales Agent Report'

    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    quote_status = fields.Selection(STATES, required=True, string='Quote Status')
    pdf_xls = fields.Selection([('pdf', 'PDF'), ('xls', 'XLSX')], string='PDF/XLSX')
    sales_agent_ids = fields.Many2many('res.users', string='Sales Agent')
    field_ids = fields.Many2many('ir.model.fields', string='Fields', domain=[('model_id', '=', 'shipment.quote')])
    remarks = fields.Text()

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        shipment_fields = self.env['ir.model.fields'].sudo().search([
            ('model_id', '=', 'shipment.quote'),
            ('name', 'in', [
                'date', 'name', 'client_id', 'estimated_total_revenue', 'estimated_total_cost', 'estimated_profit', 'origin_un_location_id', 'destination_un_location_id', 'shipment_type_id',
                'transport_mode_id', 'cargo_type_id'])
        ])
        if shipment_fields:
            res['field_ids'] = shipment_fields.ids
        return res

    def print_pdf(self):
        data = {
            'model_id': self.id,
            'from_date': self.from_date,
            'to_date': self.to_date,
        }
        return self.env.ref('fm_quote_reports.action_report_sales_agent').report_action(self, data=data)

    def print_xls(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)

        line_style = workbook.add_format({'align': 'center'})
        heading_style_1 = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '20'})
        heading_style_2 = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '10'})
        heading_style_3 = workbook.add_format({'align': 'left', 'bold': True, 'font_size': '10', 'bg_color': '#E2E2E0'})
        heading_style_4 = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '10', 'bg_color': '#E2E2E0'})

        footer_style_1 = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '12'})
        footer_style_2 = workbook.add_format({'align': 'left', 'bold': True, 'font_size': '8'})
        footer_style_3 = workbook.add_format({'align': 'right', 'bold': True, 'font_size': '8'})
        footer_style_4 = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '10'})
        worksheet = workbook.add_worksheet('Sales Agent Report')
        lang = get_lang(self.env, self.env.user.lang)
        date_format = lang.date_format
        from_date = self.from_date.strftime(date_format)
        to_date = self.to_date.strftime(date_format)
        worksheet.merge_range(1, 0, 0, len(self.sudo().field_ids), 'Sales Agent Report', heading_style_1)
        worksheet.merge_range(2, 0, 2, len(self.sudo().field_ids), from_date + ' - ' + to_date, heading_style_2)
        worksheet.set_column(0, len(self.sudo().field_ids), 18)
        col = 0
        row = 3

        est_total_revenue_place = 0
        est_total_cost = 0
        est_profit = 0

        for field in self.sudo().field_ids:
            worksheet.write(3, col, field.field_description, heading_style_2)
            col += 1

        worksheet.write(3, col, 'Status', heading_style_2)

        domain = [('status_change_date', '>=', self.from_date),
                  ('status_change_date', '<=', self.to_date),
                  ('status', '=', self.quote_status),
                  ('quote_id.user_id', 'in', self.sales_agent_ids.ids)]
        shipment_quote_history = self.env['shipment.quote.status.history'].search(domain)
        shipment_quote = shipment_quote_history.mapped('quote_id')
        user_list = []
        quote_list_new = []
        quote_list = {}
        transport_mode = {}
        shipment_type = {}
        cargo_type = {}
        for quote in shipment_quote:
            if quote.transport_mode_id.name in transport_mode:
                transport_mode[quote.transport_mode_id.name] += quote.estimated_profit
            else:
                transport_mode.update({quote.transport_mode_id.name: quote.estimated_profit})
            if quote.shipment_type_id.name in shipment_type:
                shipment_type[quote.shipment_type_id.name] += quote.estimated_profit
            else:
                shipment_type.update({quote.shipment_type_id.name: quote.estimated_profit})
            if quote.cargo_type_id.name in cargo_type:
                cargo_type[quote.cargo_type_id.name] += quote.estimated_profit
            else:
                cargo_type.update({quote.cargo_type_id.name: quote.estimated_profit})

            shipment_history = quote.status_history_ids.search([
                ('status_change_date', '>=', self.from_date), ('status_change_date', '<=', self.to_date),
                ('status', '=', self.quote_status), ('quote_id.user_id', 'in', self.sales_agent_ids.ids),
                ('quote_id', '=', quote.id)], limit=1)
            status = dict(shipment_history._fields['status'].selection).get(shipment_history.status)
            if not shipment_history:
                continue
            if quote.user_id in user_list:
                quote_list = {}
                for field_name in self.sudo().field_ids.mapped('name'):
                    if field_name == 'date':
                        quote_list.update({field_name: shipment_history.status_change_date.date()})
                    elif field_name == 'status':
                        quote_list.update({field_name: status})
                    elif 'date' in field_name:
                        quote_list.update({field_name: quote.mapped(field_name)[0]})
                    else:
                        quote_list.update({field_name: quote.mapped(field_name)})
                quote_list.update({'user_id': quote.user_id, 'status': status})
                quote_list_new.append(quote_list)
            else:
                quote_list = {}
                for field_name in self.sudo().field_ids.mapped('name'):
                    if field_name == 'date':
                        quote_list.update({field_name: shipment_history.status_change_date.date()})
                    elif field_name == 'status':
                        quote_list.update({field_name: status})
                    elif 'date' in field_name:
                        quote_list.update({field_name: quote.mapped(field_name)[0]})
                    else:
                        quote_list.update({field_name: quote.mapped(field_name)})

                    if field_name == 'estimated_total_revenue':
                        est_total_revenue_place = len(quote_list)
                    if field_name == 'estimated_total_cost':
                        est_total_cost = len(quote_list)
                    if field_name == 'estimated_profit':
                        est_profit = len(quote_list)

                quote_list.update({'user_id': quote.user_id, 'status': status})
                user_list.append(quote.user_id)
                quote_list_new.append(quote_list)
        quote_list = quote_list
        users_name = user_list

        cust_total_record = {}
        estimated_profit_record = {}
        estimated_revenue_record = {}
        estimated_cost_record = {}
        row = 4
        for uname in users_name:
            user_quote_total = 0
            estimated_total_revenue = 0
            estimated_total_cost = 0
            estimated_profit = 0
            for quote_lst in quote_list_new:
                if quote_lst.get('user_id'):
                    if quote_lst.get('user_id') == uname:
                        user_quote_total += 1
                if quote_lst.get('user_id') == uname:
                    if quote_lst.get('estimated_total_revenue'):
                        estimated_total_revenue = (estimated_total_revenue + quote_lst.get('estimated_total_revenue')[0])
                    if quote_lst.get('estimated_total_cost'):
                        estimated_total_cost = (estimated_total_cost + quote_lst.get('estimated_total_cost')[0])
                    if quote_lst.get('estimated_profit'):
                        estimated_profit = (estimated_profit + quote_lst.get('estimated_profit')[0])
            cust_total_record.update({uname.name: user_quote_total})
            estimated_profit_record.update({uname.name: estimated_profit})
            estimated_revenue_record.update({uname.name: estimated_total_revenue})
            estimated_cost_record.update({uname.name: estimated_total_cost})

            worksheet.write(row, 0, uname.name + ' (' + str(user_quote_total) + ')', heading_style_3)
            worksheet.write(row, est_total_revenue_place-1, estimated_total_revenue, heading_style_4)
            worksheet.write(row, est_total_cost-1, estimated_total_cost, heading_style_4)
            worksheet.write(row, est_profit-1, estimated_profit, heading_style_4)

            row = (row + 1)
            col_len = len(self.sudo().field_ids) + 1
            for qlist in quote_list_new:
                col = 0
                for key, val in qlist.items():
                    if uname == qlist.get('user_id'):
                        if key == 'user_id':
                            if 'user_id' in self.sudo().field_ids.mapped('name'):
                                worksheet.write(row, col, val.name, line_style)
                            else:
                                continue
                        elif 'ids' in key:
                            val = val and val.ids or ''
                            val = str(val)
                            worksheet.write(row, col, val, line_style)
                        elif key == 'id':
                            val = val and val[0] or ''
                            worksheet.write(row, col, val, line_style)
                        elif 'id' in key:
                            val = val and val.sudo().name or ''
                            worksheet.write(row, col, val, line_style)
                        elif 'date' in key:
                            if val == False:
                                date = val
                            elif val == True:
                                date = val
                            else:
                                date = val and val.strftime(date_format) or False
                            worksheet.write(row, col, date, line_style)
                        elif 'status' in key:
                            worksheet.write(row, col, val, line_style)
                        elif 'image' in key:
                            worksheet.write(row, col, '', line_style)
                        elif key in ['estimated_pickup', 'expected_delivery']:
                            if val[0] == False:
                                val = val[0]
                            else:
                                val = val and val[0].strftime(date_format) or False
                            worksheet.write(row, col, val, line_style)
                        else:
                            worksheet.write(row, col, val[0], line_style)
                        col += 1
                if uname == qlist.get('user_id'):
                    row += 1

        total_est_revenue = 0
        for key, value in estimated_revenue_record.items():
            total_est_revenue += value
        total_cost_revenue = 0
        for key, value in estimated_cost_record.items():
            total_cost_revenue += value
        total_profit_revenue = 0
        for key, value in estimated_profit_record.items():
            total_profit_revenue += value

        col = 0
        row += 1
        worksheet.write(row, col, 'SALES TEAM', footer_style_1)
        col = col+1
        worksheet.write(row, col, 'Estimated Profit', footer_style_1)
        col = col+2
        worksheet.write(row, col, 'Estimated Total Revenue', footer_style_2)
        col = col+1
        worksheet.write(row, col, total_est_revenue, footer_style_3)
        row = row+1
        col = col-1
        worksheet.write(row, col, 'Estimated Total Cost', footer_style_2)
        col = col+1
        worksheet.write(row, col, total_cost_revenue, footer_style_3)
        row = row+1
        col = col-1
        worksheet.write(row, col, 'Estimated Profit', footer_style_2)
        col = col+1
        worksheet.write(row, col, total_profit_revenue, footer_style_3)

        row = row+1
        col = 4
        worksheet.merge_range(row, col, row, 3, 'TOTAL CONFIRMED JOBS', footer_style_4)
        worksheet.merge_range(row+1, col, row+1, 3, len(quote_list_new), footer_style_4)

        row = row-2
        col = 0
        for key, value in cust_total_record.items():
            worksheet.write(row, col, key + ' (' + str(value) + ')', footer_style_2)
            row = row+1
        row = (row-(len(cust_total_record)))
        col = col+1
        total_ep = 0
        for key, value in estimated_profit_record.items():
            worksheet.write(row, col, str(value), footer_style_3)
            total_ep += value
            row = row+1

        col = 0
        worksheet.write(row, col, 'TOTAL EP', footer_style_2)
        col = col+1
        worksheet.write(row, col, total_ep, footer_style_3)
        row = row+2
        worksheet.write(row, 0, 'Transport Mode', footer_style_1)
        worksheet.write(row, 1, 'Estimated Profit', footer_style_1)
        row = row+1
        col = 0
        for key, val in transport_mode.items():
            worksheet.write(row, col, key or '', footer_style_2)
            worksheet.write(row, col+1, val, footer_style_3)
            row = row+1
        row = row+1
        worksheet.write(row, 0, 'Shipment Type', footer_style_1)
        worksheet.write(row, 1, 'Estimated Profit', footer_style_1)
        row = row+1
        col = 0
        for key, val in shipment_type.items():
            worksheet.write(row, col, key or '', footer_style_2)
            worksheet.write(row, col+1, val, footer_style_3)
            row = row+1
        row = row+1
        worksheet.write(row, 0, 'Cargo Type', footer_style_1)
        worksheet.write(row, 1, 'Estimated Profit', footer_style_1)
        row = row+1
        col = 0
        for key, val in cargo_type.items():
            worksheet.write(row, col, key or '', footer_style_2)
            worksheet.write(row, col+1, val, footer_style_3)
            row = row+1

        workbook.close()
        filename = 'Sales Agent Report %s-%s' % (self.from_date.strftime(date_format), self.to_date.strftime(date_format))
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
