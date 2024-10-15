import io
import base64
from odoo.tools.misc import xlsxwriter
from odoo.tools import format_amount

from odoo import models, _


class MixinFreightShipment(models.AbstractModel):
    _inherit = 'freight.shipment.mixin'

    def excel_set_shipment_specific_header(self, workbook, worksheet, row, shipment):
        return row

    def excel_set_charges_header(self, workbook, worksheet, row):
        heading_style = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '11', 'valign': 'vcenter'})
        # Write the headers with locked formatting
        headers = [
            _('Sr. No.'), _('Charge Name'), _('Estimated Revenue (Ext. Tax)'), _('Actual Revenue (Ext. Tax)'), _('Estimated Cost (Ext. Tax)'), _('Actual Cost (Ext. Tax)'),
            _('Estimated Profit (Ext. Tax)'), _('Actual Profit (Ext. Tax)'), _('Estimated Profit %'), _('Actual Profit %')
        ]
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, heading_style)

        # Set column width
        [worksheet.set_column(1, col, 15) for col in range(0, 15)]
        row += 1
        return row

    def excel_write_charges_row(self, workbook, worksheet, row, charges, shipment):
        count = 0
        currency = shipment.currency_id

        cell_right = workbook.add_format({'align': 'right', 'valign': 'vcenter'})

        for charge_line in charges:
            count += 1
            worksheet.write(row, 0, count)
            worksheet.write(row, 1, charge_line.product_id.display_name)
            worksheet.write(row, 2, '{}'.format(format_amount(self.env, charge_line.revenue_total_amount, currency)), cell_right)
            worksheet.write(row, 3, '{}'.format(format_amount(self.env, charge_line.revenue_actual_total_amount, currency)), cell_right)
            worksheet.write(row, 4, '{}'.format(format_amount(self.env, charge_line.cost_total_amount, currency)), cell_right)
            worksheet.write(row, 5, '{}'.format(format_amount(self.env, charge_line.cost_actual_total_amount, currency)), cell_right)
            worksheet.write(row, 6, '{}'.format(format_amount(self.env, charge_line.estimated_margin, currency)), cell_right)
            worksheet.write(row, 7, '{}'.format(format_amount(self.env, charge_line.actual_margin, currency)), cell_right)
            worksheet.write(row, 8, '{} %'.format(round(charge_line.estimated_margin_percentage, 3)), cell_right)
            worksheet.write(row, 9, '{} %'.format(round(charge_line.actual_margin_percentage, 3)), cell_right)
            row += 1
        return row

    def excel_write_total_charges_row(self, workbook, worksheet, row, charges, shipment):
        currency = shipment.currency_id
        total_heading_style = workbook.add_format({'align': 'right', 'bold': True, 'font_size': '11', 'valign': 'vcenter'})
        worksheet.write(row, 1, 'Grand Total:', total_heading_style)
        worksheet.write(row, 2, '{}'.format(format_amount(self.env, sum(charges.mapped('revenue_total_amount')), currency)), total_heading_style)
        worksheet.write(row, 3, '{}'.format(format_amount(self.env, sum(charges.mapped('revenue_actual_total_amount')), currency)), total_heading_style)
        worksheet.write(row, 4, '{}'.format(format_amount(self.env, sum(charges.mapped('cost_total_amount')), currency)), total_heading_style)
        worksheet.write(row, 5, '{}'.format(format_amount(self.env, sum(charges.mapped('cost_actual_total_amount')), currency)), total_heading_style)
        worksheet.write(row, 6, '{}'.format(format_amount(self.env, sum(charges.mapped('estimated_margin')), currency)), total_heading_style)
        worksheet.write(row, 7, '{}'.format(format_amount(self.env, sum(charges.mapped('actual_margin')), currency)), total_heading_style)
        worksheet.write(row, 8, '{} %'.format(round(sum(charges.mapped('estimated_margin')) / (sum(charges.mapped('cost_total_amount')) or 1) * 100, 3)), total_heading_style)
        worksheet.write(row, 9, '{} %'.format(round(sum(charges.mapped('actual_margin')) / (sum(charges.mapped('cost_actual_total_amount')) or 1) * 100, 3)), total_heading_style)
        row += 1
        return row

    def excel_write_prefix_row(self, workbook, worksheet, row, shipment):
        return row

    def excel_write_suffix_row(self, workbook, worksheet, row, shipment):
        return row

    def get_job_cost_sheet(self):
        return self.job_costsheet_ids if hasattr(self, 'job_costsheet_ids') else False

    def action_download_grouped_job_cost_sheet(self):
        self.ensure_one()

        # Create an in-memory Excel file
        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        row = 5

        row = self.excel_write_prefix_row(workbook, worksheet, row, self)

        row = self.excel_set_shipment_specific_header(workbook, worksheet, row, self)

        row = self.excel_set_charges_header(workbook, worksheet, row)

        charges = self.get_job_cost_sheet()
        if charges:
            row = self.excel_write_charges_row(workbook, worksheet, row, charges, self)
            row = self.excel_write_total_charges_row(workbook, worksheet, row, charges, self)

        row = self.excel_write_suffix_row(workbook, worksheet, row, self)

        workbook.close()

        # Return the Excel file as an attachment
        filename = 'Shipment_JobCostSheet_%s.xlsx' % (self.name.replace('.', ''))
        return self.action_download_attachment(filename, output)

    def action_download_attachment(self, filename, output):
        # Return the Excel file as an attachment
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
