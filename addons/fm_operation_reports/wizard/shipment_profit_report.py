# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import base64
import io
import xlsxwriter
from odoo.exceptions import ValidationError
from odoo.tools.misc import format_date


class ShipmentProfitReport(models.TransientModel):
    _name = 'shipment.profit.report'
    _description = 'Shipment Profit Report'

    salesman_ids = fields.Many2many('res.users', string='Salesman')
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    transport_mode_id = fields.Many2one('transport.mode', string='Transport Mode')
    shipment_type_id = fields.Many2one('shipment.type', string='Shipment Type')
    cargo_type_id = fields.Many2one('cargo.type', domain="[('transport_mode_id', '=', transport_mode_id)]", string='Cargo Type')
    report_format = fields.Selection([('pdf', 'PDF'), ('xlsx', 'XLSX')], default='pdf', string='Report Format')
    status = fields.Selection([('active', 'Active'), ('complete', 'Completed')], string='Shipment Status')

    @api.constrains('from_date', 'to_date')
    def _check_from_date_to_date(self):
        for rec in self:
            if rec.to_date < rec.from_date:
                raise ValidationError(_('To date should not be smaller than the From date.'))

    def print_pdf_report(self):
        data = {
            'model_id': self.id,
            'from_date': self.from_date,
            'to_date': self.to_date,
        }
        return self.env.ref('fm_operation_reports.action_report_shipment_report').report_action(self, data=data)

    def print_xlsx_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)

        style_1 = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '10px'})
        style_2 = workbook.add_format({'align': 'center', 'font_size': '10px'})
        worksheet = workbook.add_worksheet('Shipment Profit Report')
        worksheet.set_column(0, 13, 20)

        company_name = self.env.company.name
        company_address = ''
        if self.env.company:
            if self.env.company.street:
                company_address += self.env.company.street
            if self.env.company.street2:
                company_address += (', ' if company_address else '') + self.env.company.street2
            if self.env.company.city:
                company_address += (', ' if company_address else '') + self.env.company.city
            if self.env.company.state_id:
                company_address += (', ' if company_address else '') + self.env.company.state_id.name
            if self.env.company.country_id:
                company_address += (', ' if company_address else '') + self.env.company.country_id.name
            if self.env.company.zip:
                company_address += (', ' if company_address else '') + self.env.company.zip
        from_date = format_date(self.env, self.from_date)
        to_date = format_date(self.env, self.to_date)
        status = dict(self._fields['status'].selection).get(self.status)
        heading_style = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '16', 'valign': 'vcenter'})
        sub_heading_style = workbook.add_format({'align': 'left', 'bold': True, 'font_size': '11', 'valign': 'vcenter'})
        status = status
        worksheet.merge_range(0, 0, 1, 13, '')
        worksheet.write(0, 0, 'Shipment Profit Report' + ' (' + from_date + ' to ' + to_date + ')', heading_style)
        worksheet.merge_range(2, 0, 2, 13, '')
        worksheet.merge_range(3, 0, 3, 13, '')
        worksheet.merge_range(4, 0, 4, 13, '')
        worksheet.write(2, 0, 'Company Name: ' + company_name, sub_heading_style)
        if company_address:
            worksheet.write(3, 0, 'Company Address: ' + company_address, sub_heading_style)
        else:
            worksheet.write(3, 0, 'Company Address:', style_1)
        if status:
            worksheet.write(4, 0, 'Shipment Status: ' + status, sub_heading_style)
        else:
            worksheet.write(4, 1, 'Shipment Status: ', sub_heading_style)
        worksheet.write(6, 0, 'Salesman', style_1)
        worksheet.write(6, 1, 'Customer', style_1)
        worksheet.write(6, 2, 'Origin', style_1)
        worksheet.write(6, 3, 'Origin Port', style_1)
        worksheet.write(6, 4, 'Destination', style_1)
        worksheet.write(6, 5, 'Destination Port', style_1)
        worksheet.write(6, 6, 'Shipment Number', style_1)
        worksheet.write(6, 7, 'PPCC', style_1)
        worksheet.write(6, 8, 'Volume', style_1)
        worksheet.write(6, 9, 'Weight', style_1)
        worksheet.write(6, 10, 'TEU', style_1)
        worksheet.write(6, 11, 'Revenue', style_1)
        worksheet.write(6, 12, 'Cost', style_1)
        worksheet.write(6, 13, 'Profit', style_1)

        domain = [('shipment_date', '>=', self.from_date), ('shipment_date', '<=', self.to_date)]
        if self.transport_mode_id:
            domain.append(('transport_mode_id', '=', self.transport_mode_id.id))
        if self.shipment_type_id:
            domain.append(('shipment_type_id', '=', self.shipment_type_id.id))
        if self.cargo_type_id:
            domain.append(('cargo_type_id', '=', self.cargo_type_id.id))
        if self.status == 'active':
            domain.append(('state', 'not in', ['cancelled', 'completed']))
        if self.status == 'complete':
            domain.append(('state', '=', 'completed'))
        if self.salesman_ids:
            domain.append(('sales_agent_id', 'in', self.salesman_ids.ids))

        status = dict(self._fields['status'].selection).get(self.status)

        house_shipments = self.env['freight.house.shipment'].search(domain)
        total_volume = 0.0
        total_weight = 0.0
        total_teu = 0
        total_revenue = 0.0
        total_cost = 0.0
        total_profit = 0.0
        row = 7
        col = 0

        if self.env.company.volume_uom_id:
            volume_uom_id = self.env.company.volume_uom_id
        else:
            volume_uom_id = self.env['uom.uom'].search([('name', '=', 'm³')])
        if self.env.company.weight_uom_id:
            weight_uom_id = self.env.company.weight_uom_id
        else:
            weight_uom_id = self.env['uom.uom'].search([('name', '=', 'kg')])

        for shipment in house_shipments:
            if shipment.payment_terms == 'ppx':
                payment_terms = 'PP'
            elif shipment.payment_terms == 'ccx':
                payment_terms = 'CC'
            else:
                payment_terms = ''
            cost = shipment.estimated_cost
            profit = (shipment.estimated_revenue - cost)

            salesman = shipment.sales_agent_id and shipment.sales_agent_id.sudo().name or ''
            customer = shipment.client_id and shipment.client_id.sudo().name or ''
            origin = shipment.origin_un_location_id and shipment.origin_un_location_id.name or ''
            origin_port = shipment.origin_port_un_location_id and shipment.origin_port_un_location_id.code or ''
            destination = shipment.destination_un_location_id and shipment.destination_un_location_id.name or ''
            destination_port = shipment.destination_port_un_location_id and shipment.destination_port_un_location_id.code or ''
            shipment_number = shipment.booking_nomination_no
            payment_terms = payment_terms

            if shipment.volume_unit_uom_id != self.env.company.volume_uom_id:
                volume = shipment.volume_unit_uom_id._compute_quantity(shipment.volume_unit, volume_uom_id)
            else:
                volume = shipment.volume_unit
            volume_unit_uom_id = shipment.volume_unit_uom_id and shipment.volume_unit_uom_id.name or ''
            if shipment.chargeable_uom_id != self.env.company.weight_uom_id:
                weight = shipment.chargeable_uom_id._compute_quantity(shipment.chargeable_kg, weight_uom_id)
            else:
                weight = shipment.chargeable_kg
            chargeable_uom_id = shipment.chargeable_uom_id and shipment.chargeable_uom_id.name or ''
            teu = shipment.teu_total
            revenue = shipment.estimated_revenue
            cost = cost or 0
            profit = profit or 0
            volumes = str(volume) + ' ' + volume_unit_uom_id
            weights = str(weight) + ' ' + chargeable_uom_id
            currency = shipment.currency_id.symbol
            revenues = currency + ' ' + str(revenue)
            costs = currency + ' ' + str(cost)
            profits = currency + ' ' + str(profit)

            worksheet.write(row, col, salesman, style_2)
            worksheet.write(row, col+1, customer, style_2)
            worksheet.write(row, col+2, origin, style_2)
            worksheet.write(row, col+3, origin_port, style_2)
            worksheet.write(row, col+4, destination, style_2)
            worksheet.write(row, col+5, destination_port, style_2)
            worksheet.write(row, col+6, shipment_number, style_2)
            worksheet.write(row, col+7, payment_terms, style_2)
            worksheet.write(row, col+8, volumes, style_2)
            worksheet.write(row, col+9, weights, style_2)
            worksheet.write(row, col+10, teu, style_2)
            worksheet.write(row, col+11, revenues, style_2)
            worksheet.write(row, col+12, costs, style_2)
            worksheet.write(row, col+13, profits, style_2)
            col = 0
            row += 1

            total_volume += volume
            total_weight += weight
            total_teu += shipment.teu_total
            total_revenue += shipment.estimated_revenue
            total_cost += cost
            total_profit += profit

        currency = self.env.company.currency_id and self.env.company.currency_id.symbol or ''
        revenues = currency + ' ' + str(round(total_revenue, 2))
        costs = currency + ' ' + str(round(total_cost, 2))
        profits = currency + ' ' + str(round(total_profit, 2))
        col = 0
        worksheet.write(row, col, 'Total Volume:', style_1)
        total_volume = str(round(total_volume, 2)) + ' ' + volume_uom_id.name
        worksheet.write(row, col+1, total_volume, style_1)
        worksheet.write(row, col+2, 'Total Weight:', style_1)
        total_weight = str(round(total_weight, 2)) + ' ' + weight_uom_id.name
        worksheet.write(row, col+3, total_weight, style_1)
        worksheet.write(row, col+4, 'Total TEU:', style_1)
        worksheet.write(row, col+5, total_teu, style_1)
        worksheet.write(row, col+6, 'Total Revenue:', style_1)
        worksheet.write(row, col+7, revenues, style_1)
        worksheet.write(row, col+8, 'Total Cost:', style_1)
        worksheet.write(row, col+9, costs, style_1)
        worksheet.write(row, col+10, 'Total Profit', style_1)
        worksheet.write(row, col+11, profits, style_1)

        workbook.close()
        filename = 'Shipment Profit Report %s-%s' % (self.from_date.strftime('%d%b%Y'), self.to_date.strftime('%d%b%Y'))
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
