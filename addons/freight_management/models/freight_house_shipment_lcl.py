import base64
import io
import logging
import xlrd
import datetime
from itertools import groupby

from odoo import models, _
from odoo.tools.misc import xlsxwriter

_logger = logging.getLogger(__name__)


class FreightHouseShipmentLCL(models.Model):
    _inherit = 'freight.house.shipment'

    def get_package_template_column_names(self):
        columns = [
            # Package Columns
            'Package Type', 'Pack Count', 'Container Number', 'Actual Seal', 'Customs Seal',
            'MarksNums', 'UN#',
            # Commodity Columns
            'Commodity', 'L (Commodity)', 'W (Commodity)', 'H (Commodity)', 'Dimensions UOM (Commodity)', 'Pieces (Commodity)', 'Pieces UOM (Commodity)',
            'Gross Weight (Commodity)', 'Gross Weight UOM (Commodity)', 'Volume (Commodity)', 'Volume UOM (Commodity)', 'Volumetric Weight (Commodity)', 'Volumetric Weight UOM (Commodity)',
            'Net Weight (Commodity)', 'Net Weight UOM (Commodity)', 'Shipping Bill No. (Commodity)', 'Shipping Bill Date (Commodity) (YYYY-MM-DD)', 'Shipper Ref. No (Commodity)',
            'Customer Order No. (Commodity)', 'Customer Order Date (Commodity) (YYYY-MM-DD)', 'Remarks (Commodity)'
        ]
        if 'Air' not in self.transport_mode_id.name:
            columns.insert(6, 'Is HAZ')
            columns.insert(7, 'HAZ Class')
        return columns

    def get_package_template_required_columns(self):
        return ['Package Type', 'Pack Count', ]

    def get_commodity_template_required_columns(self):
        return ['Commodity', 'Pieces UOM (Commodity)', 'Gross Weight UOM (Commodity)', 'Volume UOM (Commodity)', 'Volumetric Weight (Commodity)']

    def add_selection_data_to_commodity_download_sheet(self, hidden_worksheet, worksheet, column_names, last_column_index):
        # Commodity Data Dropdown
        last_column_index += 1
        commodity_data_column_name = xlsxwriter.utility.xl_col_to_name(last_column_index)
        commodity_data = self.env['freight.commodity'].search([]).mapped('name')
        hidden_worksheet.write_column('{}2'.format(commodity_data_column_name), commodity_data)
        # worksheet.set_column('{}:XFD'.format(commodity_data_column_name), None, None, {'hidden': 1})

        # Pieces UOM Data Dropdown
        last_column_index += 1
        pieces_uom_data_column_name = xlsxwriter.utility.xl_col_to_name(last_column_index)
        pieces_uom_data = self.get_package_uom_value(
            [('category_id', '=', self.env.ref('freight_base.product_uom_categ_pack').id)])
        hidden_worksheet.write_column('{}2'.format(pieces_uom_data_column_name), pieces_uom_data)
        # worksheet.set_column('{}:XFD'.format(pieces_uom_data_column_name), None, None, {'hidden': 1})

        # Gross Weight UOM Data Dropdown
        last_column_index += 1
        gross_weight_uom_data_column_name = xlsxwriter.utility.xl_col_to_name(last_column_index)
        gross_weight_uom_data = self.get_package_uom_value(
            [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)])
        hidden_worksheet.write_column('{}2'.format(gross_weight_uom_data_column_name), gross_weight_uom_data)
        # worksheet.set_column('{}:XFD'.format(gross_weight_uom_data_column_name), None, None, {'hidden': 1})

        # Volume UOM Data Dropdown
        last_column_index += 1
        volume_uom_data_column_name = xlsxwriter.utility.xl_col_to_name(last_column_index)
        volume_uom_data = self.get_package_uom_value(
            [('category_id', '=', self.env.ref('uom.product_uom_categ_vol').id)])
        hidden_worksheet.write_column('{}2'.format(volume_uom_data_column_name), volume_uom_data)
        # worksheet.set_column('{}:XFD'.format(volume_uom_data_column_name), None, None, {'hidden': 1})

        # Dimension UOM Data Dropdown
        last_column_index += 1
        dimension_uom_data_column_name = xlsxwriter.utility.xl_col_to_name(last_column_index)
        dimension_uom_data = self.get_package_uom_value([('category_id', '=', self.env.ref('uom.uom_categ_length').id)])
        hidden_worksheet.write_column('{}2'.format(dimension_uom_data_column_name), dimension_uom_data)
        # worksheet.set_column('{}:XFD'.format(dimension_uom_data_column_name), None, None, {'hidden': 1})

        # Net Weight UOM Data Dropdown
        last_column_index += 1
        net_weight_uom_data_column_name = xlsxwriter.utility.xl_col_to_name(last_column_index)
        net_weight_uom_data = self.get_package_uom_value(
            [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)])
        hidden_worksheet.write_column('{}2'.format(net_weight_uom_data_column_name), net_weight_uom_data)
        # worksheet.set_column('{}:XFD'.format(gross_weight_uom_data_column_name), None, None, {'hidden': 1})

        # Commodity Type data validations
        if commodity_data:
            column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Commodity'))
            commodity_rows = "{0}2:{0}200".format(column_name)
            commodity_source_column = "='datavalidation'!${0}$2:${0}${1}".format(commodity_data_column_name, len(commodity_data) + 1)
            commodity_value_rule = {
                'validate': 'list',
                'source': commodity_source_column,
                'input_title': 'Commodity',
                'input_message': _('Select a Commodity type from the list'),
            }
            worksheet.data_validation(commodity_rows, commodity_value_rule)

        # Pieces UOM data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Pieces UOM (Commodity)'))
        pieces_uom_rows = "{0}2:{0}200".format(column_name)
        pieces_uom_column = "='datavalidation'!${0}$2:${0}${1}".format(pieces_uom_data_column_name, len(pieces_uom_data) + 1)
        pieces_value_rule = {
            'validate': 'list',
            'source': pieces_uom_column,
            'input_title': 'Pieces Unit UOM',
            'input_message': _('Select a pieces uom from the list'),
        }
        worksheet.data_validation(pieces_uom_rows, pieces_value_rule)

        # Dimension UOM data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Dimensions UOM (Commodity)'))
        dimension_uom_rows = "{0}2:{0}200".format(column_name)
        dimension_uom_column = "='datavalidation'!${0}$2:${0}${1}".format(dimension_uom_data_column_name, len(dimension_uom_data) + 1)
        dimension_value_rule = {
            'validate': 'list',
            'source': dimension_uom_column,
            'input_title': 'Dimension Unit UOM',
            'input_message': _('Select a dimension uom from the list'),
        }
        worksheet.data_validation(dimension_uom_rows, dimension_value_rule)

        # Gross Weight UOM data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Gross Weight UOM (Commodity)'))
        gross_weight_uom_rows = "{0}2:{0}200".format(column_name)
        gross_weight_uom_column = "='datavalidation'!${0}$2:${0}${1}".format(gross_weight_uom_data_column_name, len(gross_weight_uom_data) + 1)
        gross_weight_value_rule = {
            'validate': 'list',
            'source': gross_weight_uom_column,
            'input_title': 'Gross Weight UOM',
            'input_message': _('Select a gross_weight uom from the list'),
        }
        worksheet.data_validation(gross_weight_uom_rows, gross_weight_value_rule)

        # Volume UOM data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Volume UOM (Commodity)'))
        volume_uom_rows = "{0}2:{0}200".format(column_name)
        volume_uom_column = "='datavalidation'!${0}$2:${0}${1}".format(volume_uom_data_column_name, len(volume_uom_data) + 1)
        volume_value_rule = {
            'validate': 'list',
            'source': volume_uom_column,
            'input_title': 'Volume UOM',
            'input_message': _('Select a volume uom from the list'),
        }
        worksheet.data_validation(volume_uom_rows, volume_value_rule)

        # Volumetric Weight UOM data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Volumetric Weight UOM (Commodity)'))
        gross_weight_uom_rows = "{0}2:{0}200".format(column_name)
        gross_weight_uom_column = "='datavalidation'!${0}$2:${0}${1}".format(gross_weight_uom_data_column_name, len(gross_weight_uom_data) + 1)
        gross_weight_value_rule = {
            'validate': 'list',
            'source': gross_weight_uom_column,
            'input_title': 'Volumetric Weight UOM',
            'input_message': _('Select a volumetric weight uom from the list'),
        }
        worksheet.data_validation(gross_weight_uom_rows, gross_weight_value_rule)

        # Weight data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Gross Weight (Commodity)'))
        volume_rows = "{0}2:{0}200".format(column_name)
        worksheet.data_validation(volume_rows, self.xls_decimal_data_validation())

        # Volume data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Volume (Commodity)'))
        volume_rows = "{0}2:{0}200".format(column_name)
        worksheet.data_validation(volume_rows, self.xls_decimal_data_validation())

        # Volumetric Weight data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Volumetric Weight (Commodity)'))
        volume_rows = "{0}2:{0}200".format(column_name)
        worksheet.data_validation(volume_rows, self.xls_decimal_data_validation())

        # Length data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('L (Commodity)'))
        volume_rows = "{0}2:{0}200".format(column_name)
        worksheet.data_validation(volume_rows, self.xls_decimal_data_validation())

        # Width data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('W (Commodity)'))
        volume_rows = "{0}2:{0}200".format(column_name)
        worksheet.data_validation(volume_rows, self.xls_decimal_data_validation())

        # Height data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('H (Commodity)'))
        volume_rows = "{0}2:{0}200".format(column_name)
        worksheet.data_validation(volume_rows, self.xls_decimal_data_validation())

        # Pieces data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Pieces (Commodity)'))
        volume_rows = "{0}2:{0}200".format(column_name)
        worksheet.data_validation(volume_rows, self.xls_decimal_data_validation())

        # Net Weight UOM data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Net Weight UOM (Commodity)'))
        net_weight_uom_rows = "{0}2:{0}200".format(column_name)
        net_weight_uom_column = "='datavalidation'!${0}$2:${0}${1}".format(net_weight_uom_data_column_name, len(net_weight_uom_data) + 1)
        net_weight_value_rule = {
            'validate': 'list',
            'source': net_weight_uom_column,
            'input_title': 'Net Weight UOM',
            'input_message': _('Select a net weight uom from the list'),
        }
        worksheet.data_validation(net_weight_uom_rows, net_weight_value_rule)

        # Data Validation Rule: Date format
        date_rule = {
            'validate': 'date',
            'criteria': '>',
            'value': datetime.datetime.strptime('0600-01-30', "%Y-%m-%d"),
            'error_message': _('Only valid-date allowed in YYYY-MM-DD format')
        }
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Shipping Bill Date (Commodity) (YYYY-MM-DD)'))
        date_rows = "{0}2:{0}200".format(column_name)
        worksheet.data_validation(date_rows, date_rule)
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Customer Order Date (Commodity) (YYYY-MM-DD)'))
        date_rows = "{0}2:{0}200".format(column_name)
        worksheet.data_validation(date_rows, date_rule)

    def add_selection_data_to_package_download_sheet(self, hidden_worksheet, worksheet, column_names, last_column_index):
        # Package Type Data Dropdown
        package_type_data_column_name = xlsxwriter.utility.xl_col_to_name(last_column_index)
        domain = ['|', ('transport_mode_ids', '=', self.transport_mode_id.id), ('transport_mode_ids', '=', False),
                  ('category_id', '=', self.env.ref('freight_base.product_uom_categ_pack').id)]
        package_type_data = self.get_package_uom_value(domain)
        hidden_worksheet.write_column('{}2'.format(package_type_data_column_name), package_type_data)
        # worksheet.set_column('{}:XFD'.format(package_type_data_column_name), None, None, {'hidden': 1})

        # HAZ Class Dropdown
        last_column_index += 1
        haz_class_data_column_name = xlsxwriter.utility.xl_col_to_name(last_column_index)
        haz_class_data = self.env['haz.sub.class.code'].search([]).mapped('name')
        hidden_worksheet.write_column('{}2'.format(haz_class_data_column_name), haz_class_data)
        # worksheet.set_column('{}:XFD'.format(haz_class_data_column_name), None, None, {'hidden': 1})

        # Package Type data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Package Type'))
        package_type_rows = "{0}2:{0}200".format(column_name)
        package_type_source_column = "='datavalidation'!${0}$2:${0}${1}".format(package_type_data_column_name, len(package_type_data) + 1)
        package_type_value_rule = {
            'validate': 'list',
            'source': package_type_source_column,
            'input_title': 'Package Type',
            'input_message': _('Select a Package type from the list'),
        }
        worksheet.data_validation(package_type_rows, package_type_value_rule)

        # HAZ Class data validations
        if 'HAZ Class' in column_names:
            column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('HAZ Class'))
            haz_class_rows = "{0}2:{0}200".format(column_name)
            haz_source_column = "='datavalidation'!${0}$2:${0}${1}".format(haz_class_data_column_name, len(haz_class_data) + 1)
            haz_class_value_rule = {
                'validate': 'list',
                'source': haz_source_column,
                'input_title': 'HAZ Class',
                'input_message': _('Select a HAZ class from the list'),
            }
            worksheet.data_validation(haz_class_rows, haz_class_value_rule)

        # Pack Count data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Pack Count'))
        volume_rows = "{0}2:{0}200".format(column_name)
        worksheet.data_validation(volume_rows, self.xls_decimal_data_validation())

        self.add_selection_data_to_commodity_download_sheet(hidden_worksheet, worksheet, column_names, last_column_index)

    def action_download_lcl_package_template(self):
        self.ensure_one()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        worksheet = workbook.add_worksheet("Package Details")
        hidden_worksheet = workbook.add_worksheet('DataValidation')

        heading_style = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '12px', 'border': 1})
        heading_required_style = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '12px', 'border': 1,
                                                      'bg_color': '#D2D2FF'})
        body_style = workbook.add_format({'font_size': '12px', 'border': 1})
        date_format = workbook.add_format({'valign': 'vcenter', 'num_format': 'yyyy/mm/dd'})

        heading_col = 0
        column_names = self.get_package_template_column_names()
        for column_name in column_names:
            style = heading_style
            if column_name in self.get_package_template_required_columns():
                style = heading_required_style
            worksheet.write(0, heading_col, column_name, style)
            worksheet.set_column(0, heading_col, 30)
            heading_col += 1

        row = 1
        last_column_index = len(column_names)
        self.add_selection_data_to_package_download_sheet(hidden_worksheet, worksheet, column_names, last_column_index)
        for package_id in self.package_ids:
            if package_id.commodity_ids:
                package_line = True
                for commodity_id in package_id.commodity_ids:
                    commodity_column_index = column_names.index('Commodity')
                    if package_line:
                        worksheet.write(row, 0, package_id.package_type_id.name, body_style)  # A
                        worksheet.write(row, 1, package_id.quantity, body_style)  # B
                        worksheet.write(row, 2, package_id.container_number.container_number or '', body_style)  # C
                        worksheet.write(row, 3, package_id.seal_number or '', body_style)  # D
                        worksheet.write(row, 4, package_id.customs_seal_number or '', body_style)  # E
                        worksheet.write(row, 5, package_id.marksnnums or '', body_style)  # F
                        if 'Air' not in self.transport_mode_id.name:
                            worksheet.write_boolean(row, 6, package_id.is_hazardous, body_style)  # G
                            worksheet.write(row, 7, package_id.haz_class_id.name, body_style)  # H
                            worksheet.write(row, 8, package_id.un_code or '', body_style)  # I
                        else:
                            worksheet.write(row, 6, package_id.un_code or '', body_style)
                        worksheet.write(row, commodity_column_index, commodity_id.commodity_id.name, body_style)  # J
                        worksheet.write(row, commodity_column_index + 1, commodity_id.length, body_style)  # K
                        worksheet.write(row, commodity_column_index + 2, commodity_id.width, body_style)  # L
                        worksheet.write(row, commodity_column_index + 3, commodity_id.height, body_style)  # M
                        worksheet.write(row, commodity_column_index + 4, commodity_id.dimension_uom_id.name or '', body_style)  # N
                        worksheet.write(row, commodity_column_index + 5, commodity_id.pieces, body_style)  # O
                        worksheet.write(row, commodity_column_index + 6, commodity_id.pack_uom_id.name, body_style)  # P
                        worksheet.write(row, commodity_column_index + 7, commodity_id.gross_weight, body_style)  # Q
                        worksheet.write(row, commodity_column_index + 8, commodity_id.weight_uom_id.name, body_style)  # R
                        worksheet.write(row, commodity_column_index + 9, commodity_id.volume, body_style)  # S
                        worksheet.write(row, commodity_column_index + 10, commodity_id.volume_uom_id.name, body_style)  # T
                        worksheet.write(row, commodity_column_index + 11, commodity_id.volumetric_weight, body_style)  # U
                        worksheet.write(row, commodity_column_index + 12, commodity_id.volumetric_weight_uom_id.name, body_style)  # V
                        worksheet.write(row, commodity_column_index + 13, commodity_id.net_weight, body_style)  # W
                        worksheet.write(row, commodity_column_index + 14, commodity_id.net_weight_unit_uom_id.name, body_style)  # X
                        worksheet.write(row, commodity_column_index + 15, commodity_id.shipping_bill_no or '', body_style)  # Y
                        worksheet.write(row, commodity_column_index + 16, commodity_id.shipping_bill_date and commodity_id.shipping_bill_date.strftime("%Y-%m-%d") or '', date_format)  # Z
                        worksheet.write(row, commodity_column_index + 17, commodity_id.shipper_ref_number or '', body_style)  # AA
                        worksheet.write(row, commodity_column_index + 18, commodity_id.customer_order_no or '', body_style)  # AB
                        worksheet.write(row, commodity_column_index + 19, commodity_id.order_received_date and commodity_id.order_received_date.strftime("%Y-%m-%d") or '', date_format)  # AC
                        worksheet.write(row, commodity_column_index + 20, commodity_id.remarks or '', body_style)  # AD
                        package_line = False
                        worksheet.write(row, 100, commodity_id.id, body_style)  # CW
                    else:
                        worksheet.write(row, 0, package_id.package_type_id.name, body_style)  # A
                        worksheet.write(row, 1, package_id.quantity, body_style)  # B
                        worksheet.write(row, 2, package_id.container_number.container_number or '', body_style)  # C
                        worksheet.write(row, commodity_column_index, commodity_id.commodity_id.name, body_style)  # J
                        worksheet.write(row, commodity_column_index + 1, commodity_id.length, body_style)  # K
                        worksheet.write(row, commodity_column_index + 2, commodity_id.width, body_style)  # L
                        worksheet.write(row, commodity_column_index + 3, commodity_id.height, body_style)  # M
                        worksheet.write(row, commodity_column_index + 4, commodity_id.dimension_uom_id.name or '', body_style)  # N
                        worksheet.write(row, commodity_column_index + 5, commodity_id.pieces, body_style)  # O
                        worksheet.write(row, commodity_column_index + 6, commodity_id.pack_uom_id.name, body_style)  # P
                        worksheet.write(row, commodity_column_index + 7, commodity_id.gross_weight, body_style)  # Q
                        worksheet.write(row, commodity_column_index + 8, commodity_id.weight_uom_id.name, body_style)  # R
                        worksheet.write(row, commodity_column_index + 9, commodity_id.volume, body_style)  # S
                        worksheet.write(row, commodity_column_index + 10, commodity_id.volume_uom_id.name, body_style)  # T
                        worksheet.write(row, commodity_column_index + 11, commodity_id.volumetric_weight, body_style)  # U
                        worksheet.write(row, commodity_column_index + 12, commodity_id.volumetric_weight_uom_id.name, body_style)  # V
                        worksheet.write(row, commodity_column_index + 13, commodity_id.net_weight, body_style)  # W
                        worksheet.write(row, commodity_column_index + 14, commodity_id.net_weight_unit_uom_id.name, body_style)  # X
                        worksheet.write(row, commodity_column_index + 15, commodity_id.shipping_bill_no or '', body_style)  # Y
                        worksheet.write(row, commodity_column_index + 16, commodity_id.shipping_bill_date and commodity_id.shipping_bill_date.strftime("%Y-%m-%d") or '', date_format)  # Z
                        worksheet.write(row, commodity_column_index + 17, commodity_id.shipper_ref_number or '', body_style)  # AA
                        worksheet.write(row, commodity_column_index + 18, commodity_id.customer_order_no or '', body_style)  # AB
                        worksheet.write(row, commodity_column_index + 19, commodity_id.order_received_date and commodity_id.order_received_date.strftime("%Y-%m-%d") or '', date_format)  # AC
                        worksheet.write(row, commodity_column_index + 20, commodity_id.remarks or '', body_style)  # AD
                        worksheet.write(row, 100, commodity_id.id, body_style)  # CW

                    row += 1
            else:
                worksheet.write(row, 0, package_id.package_type_id.name, body_style)  # A
                worksheet.write(row, 1, package_id.quantity, body_style)  # B
                worksheet.write(row, 2, package_id.container_number.container_number or '', body_style)  # C
                worksheet.write(row, 3, package_id.seal_number or '', body_style)  # D
                worksheet.write(row, 4, package_id.customs_seal_number or '', body_style)  # E
                worksheet.write(row, 5, package_id.marksnnums or '', body_style)  # F
                if 'Air' not in self.transport_mode_id.name:
                    worksheet.write_boolean(row, 6, package_id.is_hazardous, body_style)  # G
                    worksheet.write(row, 7, package_id.haz_class_id.name, body_style)  # H
                    worksheet.write(row, 8, package_id.un_code or '', body_style)  # I
                else:
                     worksheet.write(row, 6, package_id.un_code or '', body_style)  # G
                row += 1
        hidden_worksheet.hide()
        workbook.close()

        file_name = '%s-PackageList.xlsx' % (self.name.replace('/', '-'))
        xlsx_base64 = base64.b64encode(output.getvalue())

        self.write({'lcl_package_data_file_name': file_name, 'lcl_package_data_file': xlsx_base64})
        url = '/web/content/%s/%s/%s/%s' % (self._name, self.id, 'lcl_package_data_file', file_name.replace(' ', ''))
        return {'type': 'ir.actions.act_url', 'url': url}

    def action_upload_lcl_package_data(self, **kwargs):

        self.ensure_one()
        self.upload_file_message = False
        attachment = self.env['ir.attachment'].sudo().browse(kwargs.get('attachment_ids', []))
        if not attachment:
            self.upload_file_message = 'File not uploaded properly. Please check file and upload file again!'
            return True

        try:
            workbook = xlrd.open_workbook(file_contents=base64.b64decode(attachment.datas) or b'')
        except Exception as e:
            _logger.warning(e)
            if attachment and attachment.mimetype not in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','application/vnd.ms-excel']:
                attachment.unlink()
                self.upload_file_message = 'Only Excel files are accepted.'
            else:
                if attachment.description:
                    self.upload_file_message = attachment.description
                    attachment.unlink()
                else:
                    self.upload_file_message = 'Could not read file properly, Please download sample file and and upload file again!'
            workbook = False
            return True

        try:
            self._upload_lcl_package_data_from_sheet(workbook)
        except Exception as e:
            IrLogging = self.env['ir.logging'].sudo()
            IrLogging.create({
                'name': 'LCL Upload', 'type': 'server', 'dbname': '-', 'level': 'DEBUG',
                'message': e, 'path': 'LCL > Upload ', 'func': 'action_upload_lcl_package_data',
                'line': 1
            })
            _logger.warning(e)
            self.upload_file_message = 'Could not process file properly, Please validate file and upload file again!'
            return True
        return True

    def _get_package_row_data_from_xls(self, workbook, worksheet):
        header_row = []
        package_columns = self.get_package_template_column_names()
        for col in range(len(package_columns)):
            value = worksheet.cell_value(0, col)
            if value:
                header_row.append(value)
        package_row_data = {}
        for row in range(1, worksheet.nrows):
            elm = {}
            for col in range(len(package_columns)):
                value_exist = worksheet.cell_value(0, col)
                if value_exist:
                    value = worksheet.cell_value(row, col)
                    cell = worksheet.cell(row, col)
                    if cell.ctype is xlrd.XL_CELL_NUMBER:
                        is_float = cell.value % 1 != 0.0
                        value = str(cell.value) if is_float else str(int(cell.value))
                    if cell.ctype == xlrd.XL_CELL_DATE:
                        value = xlrd.xldate.xldate_as_datetime(value, workbook.datemode)
                    elm[header_row[col]] = value
            if elm:
                commodity_id = int(worksheet.cell_value(row, 100) or '0') if worksheet.ncols >= 100 else 0
                if commodity_id > 0:
                    elm['id'] = commodity_id
                package_row_data[row] = elm
        return package_row_data

    def get_commodity_id_by_name(self, name):
        return self.env['freight.commodity'].search([('name', '=', name)], limit=1).id

    def _prepare_package_vals(self, package_row):
        is_haz = package_row.get('Is HAZ')
        is_haz = self.check_boolean_value(is_haz)
        return_vals = {
            'package_type_id': self.get_uom_id_by_name(package_row.get('Package Type')),
            'quantity': package_row.get('Pack Count', 0),
            'seal_number': package_row.get('Actual Seal', False),
            'customs_seal_number': package_row.get('Customs Seal', False),
            'marksnnums': package_row.get('MarksNums', False),
            'is_hazardous': is_haz,
            'haz_class_id': self.get_haz_class_id_by_name(package_row.get('HAZ Class', False)),
            'un_code': package_row.get('UN#', False),
            'package_mode': 'package',
        }
        #We do not need container number in case of Air Transport mode
        if self.mode_type != "air":
            return_vals['container_number'] = package_row.get('Container Number', False)
            
        if package_row.get('Commodity'):
            commodity_data = {
                'commodity_id': self.get_commodity_id_by_name(package_row.get('Commodity')) or False,
                'pieces': package_row.get('Pieces (Commodity)') or False,
                'pack_uom_id': self.get_uom_id_by_name(package_row.get('Pieces UOM (Commodity)')) or False,
                'length': package_row.get('L (Commodity)') or False,
                'width': package_row.get('W (Commodity)') or False,
                'height': package_row.get('H (Commodity)') or False,
                'dimension_uom_id': self.get_uom_id_by_name(package_row.get('Dimensions UOM (Commodity)')) or False,
                'gross_weight': package_row.get('Gross Weight (Commodity)') or False,
                'weight_uom_id': self.get_uom_id_by_name(package_row.get('Gross Weight UOM (Commodity)')) or False,
                'volume': package_row.get('Volume (Commodity)') or False,
                'volume_uom_id': self.get_uom_id_by_name(package_row.get('Volume UOM (Commodity)')) or False,
                'volumetric_weight': package_row.get('Volumetric Weight (Commodity)') or False,
                'volumetric_weight_uom_id': self.get_uom_id_by_name(package_row.get('Volumetric Weight UOM (Commodity)')) or False,
                'net_weight': package_row.get('Net Weight (Commodity)') or False,
                'net_weight_unit_uom_id': self.get_uom_id_by_name(package_row.get('Net Weight UOM (Commodity)')) or False,
                'shipping_bill_no': package_row.get('Shipping Bill No. (Commodity)') or False,
                'shipping_bill_date': package_row.get('Shipping Bill Date (Commodity) (YYYY-MM-DD)') or False,
                'shipper_ref_number': package_row.get('Shipper Ref. No (Commodity)') or False,
                'customer_order_no': package_row.get('Customer Order No. (Commodity)') or False,
                'order_received_date': package_row.get('Customer Order Date (Commodity) (YYYY-MM-DD)') or False,
                'remarks': package_row.get('Remarks (Commodity)') or False,
                'id': package_row.get('id') or False,
            }
            return_vals.update({
                'commodity_data': commodity_data,
                'commodity_ids': [],
            })
        return return_vals

    def group_package_line_data(self, data, with_container=False):
        def groupby_function(d):
            if with_container:
                return d['package_type_id'], d['container_number']
            return d['package_type_id']

        return groupby(sorted(data, key=groupby_function), groupby_function)

    def _prepare_find_existing_package_line_domain(self, values):
        self.ensure_one()
        domain = [
            ('package_type_id', '=', values.get('package_type_id')),
            ('shipment_id', '=', self.id)
        ]
        if values.get('container_number'):
            domain += [('container_number.name', '=', values.get('container_number'))]
        return domain

    def _get_existing_package_line_id(self, values):
        self.ensure_one()
        return self.package_ids.search(self._prepare_find_existing_package_line_domain(values), limit=1)

    def check_lcl_validations(self, val, row, uom_list):
        upload_file_message = False
        if val:
            if val.get('is_hazardous') and not val.get('haz_class_id'):
                upload_file_message = "Row: {} doesn't contain HAZ class.".format(row + 1)
            if not val.get('package_type_id'):
                upload_file_message = "Row: {} doesn't contain Package Type.".format(row + 1)
        if uom_list:
            if not self.check_uom_values(uom_list, skip_blank=False):
                upload_file_message = "Row: {} Weight/Volume/Volumetric Weight UoM doesn't match or missing.".format(row + 1)
            commodity_data = val.get('commodity_data')
            if commodity_data:
                if not commodity_data.get('commodity_id'):
                    upload_file_message = "Row: {} doesn't contain Commodity.".format(row + 1)
                if not commodity_data.get('dimension_uom_id'):
                    upload_file_message = "Row: {} doesn't contain Dimension UoM.".format(row + 1)
        return upload_file_message if upload_file_message else False

    def _upload_lcl_package_data_from_sheet(self, workbook):
        worksheet = workbook.sheet_by_index(0)
        package_row_data = self._get_package_row_data_from_xls(workbook, worksheet)
        package_data = []
        iso_invalid_numbers = []
        without_container_number_rows = []
        invalid_package_type = []
        all_seal_numbers = []
        container_package_line_uom = {}
        upload_file_message = ''
        ShipmentContainerObj = self.env['freight.master.shipment.container.number']
        for row, package_row in package_row_data.items():
            package_type = package_row.get('Package Type')
            container_number = package_row.get('Container Number')
            seal_number = package_row.get('Actual Seal', False)
            if seal_number:
                if seal_number in all_seal_numbers:
                    upload_file_message = "Row: {} contains duplicate seal number-{} within file.".format(row + 1, seal_number)
                    break
                if ShipmentContainerObj._is_duplicate_seal_number(seal_number):
                    upload_file_message = 'Row:{} Found duplicate seal number-{} file.'.format(row + 1, seal_number)
                    break
                all_seal_numbers.append(seal_number)
            if package_type:
                if container_number:
                    valid_container_number = self._ISO_validate_container_number(container_number)
                    if valid_container_number:
                        val = self._prepare_package_vals(package_row)
                        commodity_data = val.get('commodity_data')
                        if commodity_data:
                            uom_data = '{}_{}_{}'.format(commodity_data.get('weight_uom_id'), commodity_data.get('volume_uom_id'), commodity_data.get('volumetric_weight_uom_id'))
                            if package_type not in container_package_line_uom:
                                container_package_line_uom.update({package_type: [uom_data]})
                            else:
                                container_package_line_uom[package_type].append(uom_data)
                        upload_file_message = self.check_lcl_validations(val, row, container_package_line_uom.get(package_type) or [])
                        if upload_file_message:
                            break
                        val.update({
                            'container_number': package_row.get('Container Number'),
                        })
                        package_data.append(val)
                    else:
                        iso_invalid_numbers.append(container_number)
                else:
                    val = self._prepare_package_vals(package_row)
                    commodity_data = val.get('commodity_data')
                    if commodity_data:
                        uom_data = '{}_{}_{}'.format(commodity_data.get('weight_uom_id'), commodity_data.get('volume_uom_id'), commodity_data.get('volumetric_weight_uom_id'))
                        if package_type not in container_package_line_uom:
                            container_package_line_uom.update({package_type: [uom_data]})
                        else:
                            container_package_line_uom[package_type].append(uom_data)
                    upload_file_message = self.check_lcl_validations(val, row, container_package_line_uom.get(package_type) or [])
                    if upload_file_message:
                        break
                    without_container_number_rows.append(val)
            else:
                upload_file_message = "Row: {} doesn't contain Package Type.".format(row + 1)
                invalid_package_type.append(package_type)
                break
        if upload_file_message:
            self.upload_file_message = upload_file_message
            return False
        validation_msg = []
        if invalid_package_type:
            validation_msg.append('''Invalid Package Type:\n - %s''' % (','.join(invalid_package_type)))
        if iso_invalid_numbers:
            validation_msg.append('''Invalid Container Number as per ISO 6346 Standard:\n - %s''' % (','.join(iso_invalid_numbers)))
        write_vals = []
        package_data_rows = []
        CommodityObj = self.env['freight.house.package.commodity']
        if package_data:
            grouped_data = self.group_package_line_data(package_data, with_container=True)
            for distinct_values, groupby_res in grouped_data:
                result = list(groupby_res)
                package_data = result[0]
                result = filter(lambda r: r.get('commodity_data'), result)
                commodity_ids = list(
                    map(lambda res: res.get('commodity_data') and (0, 0, res.get('commodity_data')), result))
                for commodity in commodity_ids:
                    if not commodity[2].get('id') or not CommodityObj.browse(commodity[2].get('id')).exists():
                        package_data['commodity_ids'].append(commodity)
                    else:
                        if 'existing_commodity_ids' not in package_data:
                            package_data['existing_commodity_ids'] = [commodity[2]]
                        else:
                            package_data['existing_commodity_ids'].append(commodity[2])
                package_data_rows.append(package_data)
        if without_container_number_rows:
            grouped_data = self.group_package_line_data(without_container_number_rows, with_container=False)
            for distinct_values, groupby_res in grouped_data:
                result = list(groupby_res)
                package_data = result[0]
                result = filter(lambda r: r.get('commodity_data'), result)
                commodity_ids = list(
                    map(lambda res: res.get('commodity_data') and (0, 0, res.get('commodity_data')), result))
                for commodity in commodity_ids:
                    if not commodity[2].get('id') or not CommodityObj.browse(commodity[2].get('id')).exists():
                        package_data['commodity_ids'].append(commodity)
                    else:
                        if 'existing_commodity_ids' not in package_data:
                            package_data['existing_commodity_ids'] = [commodity[2]]
                        else:
                            package_data['existing_commodity_ids'].append(commodity[2])
                package_data_rows.append(package_data)
        Package = self.env['freight.house.shipment.package']
        ContainerNumberObj = self.env['freight.master.shipment.container.number']
        for row in package_data_rows:
            data = dict(row)
            if 'existing_commodity_ids' in row:
                existing_commodities = row.pop('existing_commodity_ids')
                data.pop('existing_commodity_ids')
                for existing_commodity in existing_commodities:
                    commodity = CommodityObj.browse(existing_commodity.pop('id'))
                    commodity.write(existing_commodity)

            for key, value in data.items():
                if not hasattr(Package, key):
                    del row[key]
            existing_package_line_id = self._get_existing_package_line_id(row)
            if 'container_number' in row:
                container_number = row.pop('container_number')
                existing_container_number = ContainerNumberObj.search([('name', '=', container_number)], limit=1)
                if existing_container_number:
                    row.update({
                        'container_number': existing_container_number.id,
                    })
                else:
                    container_number_vals = {
                        'container_number': container_number,
                        # 'seal_number': row.get('seal_number'),
                        # 'customs_seal_number': row.get('customs_seal_number'),
                    }
                    container_number_id = ContainerNumberObj.create(container_number_vals)
                    row.update({
                        'container_number': container_number_id.id,
                    })
            if existing_package_line_id:
                write_vals.append((1, existing_package_line_id.id, row))
            else:
                write_vals.append((0, 0, row))
        if write_vals:
            try:
                self.write({
                    'package_ids': write_vals
                })
            except Exception as e:
                _logger.warning(e)
                validation_msg.append('Import Fail: {}'.format(e))
        if validation_msg:
            self.upload_file_message = '\n'.join(validation_msg)
        else:
            self.upload_file_message = False
