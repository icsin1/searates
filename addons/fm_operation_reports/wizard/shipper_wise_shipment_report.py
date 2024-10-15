# -*- coding: utf-8 -*-

from odoo import models, fields
import base64
import io
import xlsxwriter


class ShipperShipmentReport(models.TransientModel):
    _name = 'shipper.shipment.report'
    _description = 'Shipper Shipment Report'

    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    shipper_ids = fields.Many2many('res.partner', string='Shippers')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    def print_xlsx_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        style_1 = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '10px', 'bg_color': '#b1b1b1', 'border': 1})
        style_2 = workbook.add_format({'align': 'center', 'font_size': '10px'})
        worksheet = workbook.add_worksheet('Shipper Wise Report')
        worksheet.set_column(0, 22, 20)

        worksheet.write(0, 0, 'SHIPMENT TYPE', style_1)
        worksheet.write(0, 1, 'LOADING DATE', style_1)
        worksheet.write(0, 2, 'CUT OFF DATE', style_1)
        worksheet.write(0, 3, 'PO NUMBER', style_1)
        worksheet.write(0, 4, 'JOB NUMBER', style_1)
        worksheet.write(0, 5, 'POL', style_1)
        worksheet.write(0, 6, 'DESTINATION', style_1)
        worksheet.write(0, 7, 'SHIPPER', style_1)
        worksheet.write(0, 8, 'CONSIGNEE', style_1)
        worksheet.write(0, 9, 'BOOKING NO', style_1)
        worksheet.write(0, 10, 'CONTAINER NO', style_1)
        worksheet.write(0, 11, 'BL STATUS', style_1)
        worksheet.write(0, 12, 'VESSEL', style_1)
        worksheet.write(0, 13, 'NO OF CONTAINER', style_1)
        worksheet.write(0, 14, 'CONTAINER SIZE', style_1)
        worksheet.write(0, 15, 'INVOICE TOTAL (USD)', style_1)
        worksheet.write(0, 16, 'INVOICE TOTAL (AED)', style_1)
        worksheet.write(0, 17, 'INVOICE DATE', style_1)
        worksheet.write(0, 18, 'DUE DATE', style_1)
        worksheet.write(0, 19, 'ETD', style_1)
        worksheet.write(0, 20, 'ETA', style_1)
        worksheet.write(0, 21, 'TRANSIT TIME', style_1)
        worksheet.write(0, 22, 'REMARK', style_1)
        row = 1
        col = 0

        domain = [('shipment_date', '>=', self.from_date), ('shipment_date', '<=', self.to_date),
                  ('transport_mode_id', '=', self.env.ref('freight_base.transport_mode_sea').id)]
        if self.company_id:
            domain.append(('company_id', '=', self.company_id.id))
        if self.shipper_ids:
            domain.append(('shipper_id', 'in', self.shipper_ids.ids))
        house_shipments = self.env['freight.house.shipment'].sudo().search(domain)
        usd_currency = self.env.ref('base.USD')
        aed_currency = self.env.ref('base.AED')
        for shipment in house_shipments:
            shipment_type = shipment.shipment_type_id.name or ''
            shipment_date = shipment.shipment_date and shipment.shipment_date.strftime('%m/%d/%Y') or ''
            cut_off_date = shipment.carrier_vessel_cut_off_datetime and shipment.carrier_vessel_cut_off_datetime.strftime('%m/%d/%Y') or ''
            invoices = self.env['account.move'].sudo().search([('house_shipment_ids', 'in', shipment.ids),
                                                               ('move_type', '=', 'out_invoice')])
            po_number_list = []
            invoice_date_list = []
            invoice_due_date_list = []
            invoice_total_usd = 0
            invoice_total_aed = 0
            for invoice in invoices:
                if invoice.po_number:
                    po_number_list.append(invoice.po_number)
                if invoice.invoice_date:
                    invoice_date = invoice.invoice_date.strftime('%m/%d/%Y')
                    invoice_date_list.append(invoice_date)
                if invoice.invoice_date_due:
                    invoice_date_due = invoice.invoice_date_due.strftime('%m/%d/%Y')
                    invoice_due_date_list.append(invoice_date_due)
                if invoice.amount_total:
                    if invoice.currency_id == usd_currency:
                        invoice_total_usd += invoice.amount_total
                        invoice_total_aed = invoice.currency_id._convert(invoice.amount_total, aed_currency, self.company_id,
                                                                         fields.Date.today()) if invoice.amount_total else 0
                    elif invoice.currency_id == aed_currency:
                        invoice_total_aed += invoice.amount_total
                        invoice_total_usd = invoice.currency_id._convert(invoice.amount_total, usd_currency, self.company_id,
                                                                         fields.Date.today()) if invoice.amount_total else 0
                    else:
                        invoice_total_usd = invoice.currency_id._convert(invoice.amount_total, usd_currency, self.company_id,
                                                                         fields.Date.today()) if invoice.amount_total else 0
                        invoice_total_aed = invoice.currency_id._convert(invoice.amount_total, aed_currency, self.company_id,
                                                                         fields.Date.today()) if invoice.amount_total else 0
            po_number = ', '.join(po_number_list) if po_number_list else ''
            job_number = shipment.booking_nomination_no or ''
            pol = shipment.origin_port_un_location_id and shipment.origin_port_un_location_id.code or ''
            destination = shipment.destination_port_un_location_id and shipment.destination_port_un_location_id.code or ''
            shipper = shipment.shipper_id and shipment.shipper_id.name or ''
            consignee = shipment.consignee_id and shipment.consignee_id.name or ''
            booking_no = shipment.hbl_number or ''
            containers = shipment.container_ids or shipment.package_ids
            containers_list = []
            container_type_list = []
            for container in containers:
                if container.container_number:
                    containers_list.append(container.container_number.name)
                if container.container_type_id:
                    container_type_list.append(container.container_type_id.code)
            container_no = ', '.join(containers_list) if containers_list else ''
            bl_status = shipment.transport_mode_id and shipment.transport_mode_id.code or ''
            vessel = shipment.vessel_id and shipment.vessel_id.name or ''
            no_of_container = len(containers_list) if containers_list else 0
            container_size = ', '.join(container_type_list) if container_type_list else ''
            invoice_date = ', '.join(invoice_date_list) if invoice_date_list else ''
            invoice_due_date = ', '.join(invoice_due_date_list) if invoice_due_date_list else ''
            etd = ''
            eta = ''
            transit_time = 0
            if shipment.transport_mode_id.id == self.env.ref('freight_base.transport_mode_land').id:
                etd = shipment.etd_time and shipment.etd_time.strftime('%m/%d/%Y') or ''
                eta = shipment.etp_time and shipment.etp_time.strftime('%m/%d/%Y') or ''
                if shipment.etd_time and shipment.etp_time:
                    tt_days = shipment.etd_time.date() - shipment.etp_time.date()
                    transit_time = tt_days.days
            else:
                etd = shipment.etd_time and shipment.etd_time.strftime('%m/%d/%Y') or ''
                eta = shipment.eta_time and shipment.eta_time.strftime('%m/%d/%Y') or ''
                if shipment.etd_time and shipment.eta_time:
                    tt_days = shipment.eta_time.date() - shipment.etd_time.date()
                    transit_time = tt_days.days
            transit_time = transit_time
            remark = shipment.remark or ''

            worksheet.write(row, col, shipment_type, style_2)
            worksheet.write(row, col+1, shipment_date, style_2)
            worksheet.write(row, col+2, cut_off_date, style_2)
            worksheet.write(row, col+3, po_number, style_2)
            worksheet.write(row, col+4, job_number, style_2)
            worksheet.write(row, col+5, pol, style_2)
            worksheet.write(row, col+6, destination, style_2)
            worksheet.write(row, col+7, shipper, style_2)
            worksheet.write(row, col+8, consignee, style_2)
            worksheet.write(row, col+9, booking_no, style_2)
            worksheet.write(row, col+10, container_no, style_2)
            worksheet.write(row, col+11, bl_status, style_2)
            worksheet.write(row, col+12, vessel, style_2)
            worksheet.write(row, col+13, no_of_container, style_2)
            worksheet.write(row, col+14, container_size, style_2)
            worksheet.write(row, col+15, invoice_total_usd, style_2)
            worksheet.write(row, col+16, invoice_total_aed, style_2)
            worksheet.write(row, col+17, invoice_date, style_2)
            worksheet.write(row, col+18, invoice_due_date, style_2)
            worksheet.write(row, col+19, etd, style_2)
            worksheet.write(row, col+20, eta, style_2)
            worksheet.write(row, col+21, transit_time, style_2)
            worksheet.write(row, col+22, remark, style_2)
            col = 0
            row += 1

        workbook.close()
        filename = 'Shipper Wise Report %s-%s' % (self.from_date.strftime('%d%b%Y'), self.to_date.strftime('%d%b%Y'))
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
            'url': 'web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas&download=true&filename=%s'
                   % (attachment.id, filename),
            'target': 'new',
        }
