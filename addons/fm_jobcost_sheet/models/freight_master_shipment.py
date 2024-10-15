# -*- coding: utf-8 -*-
import io
import base64
from odoo import fields, models


class FreightMasterShipment(models.Model):
    _inherit = "freight.master.shipment"

    job_costsheet_ids = fields.One2many('master.cost.revenue.report', 'master_shipment_id')

    def excel_set_shipment_specific_header(self, workbook, worksheet, row, shipment):
        left_heading_style = workbook.add_format({'align': 'left', 'bold': True, 'font_size': '11px', 'valign': 'vcenter'})

        if shipment.company_id.logo:
            worksheet.merge_range(0, 0, row, 9, '')
            worksheet.insert_image('D1:E1', '', {'image_data': io.BytesIO(base64.b64decode(shipment.company_id.logo_512)), 'x_scale': 0.6, 'y_scale': 0.6})
            row += 1

        worksheet.merge_range(row, 0, row, 1, '')
        worksheet.merge_range(row, 2, row, 6, '')
        worksheet.write(row, 0, 'MBL: {}'.format(shipment.carrier_booking_reference_number or ''), left_heading_style)
        worksheet.write(row, 2, 'Job Cost Sheet: {}'.format(shipment.carrier_booking_reference_number or '' if shipment.carrier_booking_reference_number else shipment.name or ''), left_heading_style)
        row += 1

        worksheet.merge_range(row, 0, row, 1, '')
        worksheet.merge_range(row, 2, row, 3, '')
        worksheet.merge_range(row, 4, row, 6, '')
        worksheet.write(row, 0, 'Origin Port: {}'.format(shipment.origin_port_un_location_id.display_name), left_heading_style)
        worksheet.write(row, 2, 'Destination Port: {}'.format(shipment.destination_port_un_location_id.display_name), left_heading_style)
        worksheet.write(row, 4, 'Vessel & Voyage No: {}{}{}'.format(
            shipment.vessel_id.display_name or '', ' / ' if shipment.vessel_id and shipment.voyage_number else '', shipment.voyage_number or ''), left_heading_style)
        row += 2
        return row

    def excel_write_suffix_row(self, workbook, worksheet, row, shipment):
        left_heading_style = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '11px', 'valign': 'vcenter'})
        for house_shipment in shipment.house_shipment_ids:
            charges = house_shipment.get_job_cost_sheet()
            if charges:
                worksheet.merge_range(row, 0, row, 9, '{}'.format(house_shipment.hbl_number or '' if house_shipment.hbl_number else house_shipment.name or ''), left_heading_style)
                row += 1
                row = self.excel_write_charges_row(workbook, worksheet, row, charges, house_shipment)
                row = self.excel_write_total_charges_row(workbook, worksheet, row, charges, house_shipment)
        return row
