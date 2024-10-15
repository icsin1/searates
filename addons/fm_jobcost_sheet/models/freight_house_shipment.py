# -*- coding: utf-8 -*-
import io
import base64
from odoo import fields, models


class FreightHouseShipment(models.Model):
    _inherit = "freight.house.shipment"

    job_costsheet_ids = fields.One2many('house.cost.revenue.report', 'house_shipment_id')

    def excel_set_shipment_specific_header(self, workbook, worksheet, row, shipment):
        left_heading_style = workbook.add_format({'align': 'left', 'bold': True, 'font_size': '11px', 'valign': 'vcenter'})

        if shipment.company_id.logo:
            worksheet.merge_range(0, 0, row, 9, '')
            worksheet.insert_image('D1:E1', '', {'image_data': io.BytesIO(base64.b64decode(shipment.company_id.logo_512)), 'x_scale': 0.6, 'y_scale': 0.6})
            row += 1

        worksheet.merge_range(row, 0, row, 1, '')
        worksheet.merge_range(row, 2, row, 6, '')
        worksheet.write(row, 0, 'Master Shipment No: {}'.format(shipment.parent_id.carrier_booking_reference_number or '' if shipment.parent_id.carrier_booking_reference_number else shipment.parent_id.name or ''), left_heading_style)
        worksheet.write(row, 2, 'Job Cost Sheet: {}'.format(shipment.hbl_number or '' if shipment.hbl_number else shipment.name or ''), left_heading_style)
        row += 1

        worksheet.merge_range(row, 0, row, 1, '')
        worksheet.merge_range(row, 2, row, 3, '')
        worksheet.merge_range(row, 4, row, 6, '')
        worksheet.write(row, 0, 'Customer: {}'.format(shipment.client_id.name), left_heading_style)
        worksheet.write(row, 2, 'Shipper: {}'.format(shipment.shipper_id.name), left_heading_style)
        worksheet.write(row, 4, 'Consignee: {}'.format(shipment.consignee_id.name), left_heading_style)
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

    def action_send_jobcost_sheet(self):
        # ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        template_id = self.env['ir.model.data']._xmlid_to_res_id('fm_jobcost_sheet.email_template_charges_send_by_email', raise_if_not_found=False)
        ctxs = {
            'default_model': self._name,
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_light",
            'all_service_ids': self.ids,
        }
        return {
            'name': 'Charges: Mail Composer',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctxs,
        }
