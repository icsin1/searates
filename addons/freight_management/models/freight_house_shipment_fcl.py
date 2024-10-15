import base64
import io
import logging
import xlrd
from itertools import groupby

from odoo import models, _
from odoo.tools.misc import xlsxwriter

_logger = logging.getLogger(__name__)


class FreightHouseShipmentFCL(models.Model):
    _inherit = 'freight.house.shipment'

    def get_container_template_column_names(self):
        return ['Container Type Code', 'Container Number', 'Seal Number', 'Customs Seal',
                'Is HAZ', 'HAZ Class', 'Container Temperature', 'Container Temperature UOM',
                'Package Type (Package Group)', 'Quantity (Package Group)', 'Weight (Package Group)',
                'Weight Unit (Package Group)', 'Volume (Package Group)', 'Volume Unit (Package Group)',
                'Volumetric Weight (Package Group)', 'Volumetric Weight Unit (Package Group)',
                'Net Weight (Package Group)', 'Net Weight Unit (Package Group)', 'Description (Package Group)']

    def get_required_columns(self):
        """Add field names if it needs to be required in Container xls"""
        return ['Container Type Code']

    def action_download_container_numbers_template(self):
        self.ensure_one()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()
        hidden_worksheet = workbook.add_worksheet('DataValidation')

        heading_style = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '12px', 'border': 1})
        heading_required_style = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '12px', 'border': 1,
                                                      'bg_color': '#D2D2FF'})
        body_style = workbook.add_format({'font_size': '12px', 'border': 1})

        heading_col = 0
        column_names = self.get_container_template_column_names()
        for column_name in column_names:
            style = heading_style
            if column_name in self.get_required_columns():
                style = heading_required_style
            worksheet.write(0, heading_col, column_name, style)
            worksheet.set_column(0, heading_col, 30)
            heading_col += 1

        col = 0
        row = 1
        last_column_index = len(column_names)
        # Container Type Dropdown
        container_type_data_column_name = xlsxwriter.utility.xl_col_to_name(last_column_index)
        container_type_data = self.env['freight.container.type'].search([]).mapped('code')
        hidden_worksheet.write_column('{}2'.format(container_type_data_column_name), container_type_data)
        # worksheet.set_column('{}:XFD'.format(container_type_data_column_name), None, None, {'hidden': 1})

        # Weight UOM DropDown
        weight_uom_data_column_name = xlsxwriter.utility.xl_col_to_name(last_column_index + 1)
        weight_uom_data = self.env['uom.uom'].search(
            [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)]).mapped('name')
        hidden_worksheet.write_column('{}2'.format(weight_uom_data_column_name), weight_uom_data)
        # worksheet.set_column('{}:XFD'.format(weight_uom_data_column_name), None, None, {'hidden': 1})

        weight_unit_uom_column = "='datavalidation'!${0}$2:${0}${1}".format(weight_uom_data_column_name, len(weight_uom_data) + 1)

        # Volume UOM DropDown
        volume_uom_data_column_name = xlsxwriter.utility.xl_col_to_name(last_column_index + 2)
        volume_uom_data = self.env['uom.uom'].search(
            [('category_id', '=', self.env.ref('uom.product_uom_categ_vol').id)]).mapped('name')
        hidden_worksheet.write_column('{}2'.format(volume_uom_data_column_name), volume_uom_data)
        # worksheet.set_column('{}:XFD'.format(volume_uom_data_column_name), None, None, {'hidden': 1})

        # HAZ Class Dropdown
        haz_class_data_column_name = xlsxwriter.utility.xl_col_to_name(last_column_index + 3)
        haz_class_data = self.env['haz.sub.class.code'].search([]).mapped('name')
        hidden_worksheet.write_column('{}2'.format(haz_class_data_column_name), haz_class_data)
        # worksheet.set_column('{}:XFD'.format(haz_class_data_column_name), None, None, {'hidden': 1})

        # Package Type (Package Group) Dropdown
        package_type_data_column_name = xlsxwriter.utility.xl_col_to_name(last_column_index + 4)
        domain = ['|', ('transport_mode_ids', '=', self.transport_mode_id.id), ('transport_mode_ids', '=', False),
                  ('category_id', '=', self.env.ref('freight_base.product_uom_categ_pack').id)]
        package_type_data = self.env['uom.uom'].search(domain).mapped('name')
        hidden_worksheet.write_column('{}2'.format(package_type_data_column_name), package_type_data)
        # worksheet.set_column('{}:XFD'.format(package_type_data_column_name), None, None, {'hidden': 1})

        # Container Temperature UOM DropDown
        container_temp_uom_data_column_name = xlsxwriter.utility.xl_col_to_name(last_column_index + 1)
        container_temp_uom_data = self.env['uom.uom'].search(
            [('category_id', '=', self.env.ref('freight_base.product_uom_categ_temperature').id)]).mapped('name')
        hidden_worksheet.write_column('{}2'.format(container_temp_uom_data_column_name), container_temp_uom_data)

        # Net Weight UOM DropDown
        net_weight_uom_data_column_name = xlsxwriter.utility.xl_col_to_name(last_column_index + 1)
        net_weight_uom_data = self.env['uom.uom'].search(
            [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)]).mapped('name')
        hidden_worksheet.write_column('{}2'.format(net_weight_uom_data_column_name), net_weight_uom_data)
        # worksheet.set_column('{}:XFD'.format(weight_uom_data_column_name), None, None, {'hidden': 1})

        # data validations
        # Container Type data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Container Type Code'))
        container_type_rows = "{0}2:{0}200".format(column_name)
        container_type_source_column = "='datavalidation'!${0}$2:${0}${1}".format(container_type_data_column_name, len(container_type_data) + 1)
        container_type_value_rule = {
            'validate': 'list',
            'source': container_type_source_column,
            'input_title': 'Container Type',
            'input_message': _('Select a container type from the list'),
        }
        worksheet.data_validation(container_type_rows, container_type_value_rule)

        # HAZ Class data validations
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

        # Package Type (Package Group) data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Package Type (Package Group)'))
        package_type_rows = "{0}2:{0}200".format(column_name)
        package_type_source_column = "='datavalidation'!${0}$2:${0}${1}".format(package_type_data_column_name, len(package_type_data) + 1)
        package_type_value_rule = {
            'validate': 'list',
            'source': package_type_source_column,
            'input_title': 'Package Type',
            'input_message': _('Select a Package Type from the list'),
        }
        worksheet.data_validation(package_type_rows, package_type_value_rule)

        # Quantity (Package Group) data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Quantity (Package Group)'))
        qty_package_group_rows = "{0}2:{0}200".format(column_name)
        worksheet.data_validation(qty_package_group_rows, self.xls_decimal_data_validation())

        # Weight (Package Group) data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Weight (Package Group)'))
        weight_package_group_rows = "{0}2:{0}200".format(column_name)
        worksheet.data_validation(weight_package_group_rows, self.xls_decimal_data_validation())

        # Weight Unit (Package Group) data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Weight Unit (Package Group)'))
        weight_unit_uom_package_group_rows = "{0}2:{0}200".format(column_name)
        weight_unit_package_group_value_rule = {
            'validate': 'list',
            'source': weight_unit_uom_column,
            'input_title': 'Weight Unit UOM',
            'input_message': _('Select a weight unit from the list'),
        }
        worksheet.data_validation(weight_unit_uom_package_group_rows, weight_unit_package_group_value_rule)

        # Volume (Package Group) data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Volume (Package Group)'))
        volume_package_group_rows = "{0}2:{0}200".format(column_name)
        worksheet.data_validation(volume_package_group_rows, self.xls_decimal_data_validation())

        # Volume Unit (Package Group) data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Volume Unit (Package Group)'))
        volume_unit_uom_package_group_rows = "{0}2:{0}200".format(column_name)
        volume_unit_uom_package_group_column = "='datavalidation'!${0}$2:${0}${1}".format(volume_uom_data_column_name, len(volume_uom_data) + 1)
        volume_unit_package_group_value_rule = {
            'validate': 'list',
            'source': volume_unit_uom_package_group_column,
            'input_title': 'Volume Unit',
            'input_message': _('Select a volume unit from the list'),
        }
        worksheet.data_validation(volume_unit_uom_package_group_rows, volume_unit_package_group_value_rule)

        # Volumetric Weight (Package Group) data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Volumetric Weight (Package Group)'))
        volumetric_weight_rows = "{0}2:{0}200".format(column_name)
        worksheet.data_validation(volumetric_weight_rows, self.xls_decimal_data_validation())

        # Volumetric Unit (Package Group) data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Volumetric Weight Unit (Package Group)'))
        volumetric_weight_unit_uom_package_group_rows = "{0}2:{0}200".format(column_name)
        volumetric_weight_unit_package_group_value_rule = {
            'validate': 'list',
            'source': weight_unit_uom_column,
            'input_title': 'Weight Unit UOM',
            'input_message': _('Select a weight unit from the list'),
        }
        worksheet.data_validation(volumetric_weight_unit_uom_package_group_rows, volumetric_weight_unit_package_group_value_rule)

        # Container Temperature data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Container Temperature'))
        container_temp_rows = "{0}2:{0}200".format(column_name)
        worksheet.data_validation(container_temp_rows, self.xls_decimal_data_validation())

        # Container Temperature Unit data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Container Temperature UOM'))
        container_temp_unit_uom_rows = "{0}2:{0}200".format(column_name)
        container_temp_unit_value_rule = {
            'validate': 'list',
            'source': container_temp_uom_data,
            'input_title': 'Container Temperature UOM',
            'input_message': _('Select a container temperature uom from the list'),
        }
        worksheet.data_validation(container_temp_unit_uom_rows, container_temp_unit_value_rule)

        # Net Weight (Package Group) data validations
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Net Weight (Package Group)'))
        net_weight_rows = "{0}2:{0}200".format(column_name)
        worksheet.data_validation(net_weight_rows, self.xls_decimal_data_validation())

        # Net Weight Unit (Package Group) data validations
        net_unit_uom_column = "='datavalidation'!${0}$2:${0}${1}".format(net_weight_uom_data_column_name, len(net_weight_uom_data) + 1)
        column_name = xlsxwriter.utility.xl_col_to_name(column_names.index('Net Weight Unit (Package Group)'))
        net_weight_unit_uom_package_group_rows = "{0}2:{0}200".format(column_name)
        net_weight_unit_package_group_value_rule = {
            'validate': 'list',
            'source': net_unit_uom_column,
            'input_title': 'Net Weight Unit UOM',
            'input_message': _('Select a net unit from the list'),
        }
        worksheet.data_validation(net_weight_unit_uom_package_group_rows, net_weight_unit_package_group_value_rule)

        for record in self.container_ids:
            for package_group in record.package_group_ids:
                worksheet.write(row, col, record.container_type_id.code, body_style)  # A
                worksheet.write(row, col + 1, record.container_number.container_number or '', body_style)  # B
                worksheet.write_string(row, col + 2, record.seal_number or '', body_style)  # C
                worksheet.write_string(row, col + 3, record.customs_seal_number or '', body_style)  # D
                worksheet.write_boolean(row, col + 4, record.is_hazardous, body_style)  # E
                worksheet.write(row, col + 5, record.is_hazardous and record.haz_class_id.name or '', body_style)  # F
                worksheet.write(row, col + 6, record.container_temperature, body_style)  # G
                worksheet.write(row, col + 7, record.container_temperature_uom_id.name or '', body_style)  # H
                worksheet.write(row, col + 8, package_group.package_type_id.display_name or '', body_style)  # I
                worksheet.write(row, col + 9, package_group.quantity or 0, body_style)  # J
                worksheet.write(row, col + 10, package_group.weight_unit, body_style)  # k
                worksheet.write(row, col + 11, package_group.weight_unit_uom_id.name or '', body_style)  # L
                worksheet.write(row, col + 12, package_group.volume_unit or 0, body_style)  # M
                worksheet.write(row, col + 13, package_group.volume_unit_uom_id.name or '', body_style)  # N
                worksheet.write(row, col + 14, package_group.volumetric_weight or 0, body_style)  # O
                worksheet.write(row, col + 15, package_group.weight_volume_unit_uom_id.name or '', body_style)  # P
                worksheet.write(row, col + 16, package_group.net_weight or 0, body_style)  # Q
                worksheet.write(row, col + 17, package_group.net_weight_unit_uom_id.name or '', body_style)  # R
                worksheet.write(row, col + 18, package_group.description or '', body_style)  # S
                worksheet.write(row, 100, package_group.id, body_style)  # Add ID at cell number 100 - CW
                row += 1
            if not record.package_group_ids:
                worksheet.write(row, col, record.container_type_id.code, body_style)  # A
                worksheet.write(row, col + 1, record.container_number.container_number or '', body_style)  # B
                worksheet.write_string(row, col + 2, record.seal_number or '', body_style)  # C
                worksheet.write_string(row, col + 3, record.customs_seal_number or '', body_style)  # D
                worksheet.write_boolean(row, col + 4, record.is_hazardous, body_style)  # E
                worksheet.write(row, col + 5, record.is_hazardous and record.haz_class_id.name or '', body_style)  # F
                worksheet.write(row, col + 6, record.container_temperature, body_style)  # G
                worksheet.write(row, col + 7, record.container_temperature_uom_id.name or '', body_style)  # H
                row += 1
        hidden_worksheet.hide()
        workbook.close()

        file_name = '%s-ContainerList.xlsx' % (self.name.replace('/', '-'))
        xlsx_base64 = base64.b64encode(output.getvalue())

        # FIXME: Do Later, Use direct header instead of field on model to store file
        self.write({'container_document_file_name': file_name, 'container_number_list_file': xlsx_base64})
        url = '/web/content/%s/%s/%s/%s' % (self._name, self.id, 'container_number_list_file', file_name.replace(' ', ''))
        return {'type': 'ir.actions.act_url', 'url': url}

    def _prepare_container_vals(self, container_row):
        is_haz = container_row.get('Is HAZ')
        is_haz = self.check_boolean_value(is_haz)
        return_vals = {
            'customs_seal_number': container_row.get('Customs Seal'),
            'is_hazardous': is_haz,
            'haz_class_id': self.get_haz_class_id_by_name(container_row.get('HAZ Class')),
            'container_temperature': container_row.get('Container Temperature'),
            'container_temperature_uom_id': self.get_uom_id_by_name(container_row.get('Container Temperature UOM')),
        }
        if container_row.get('Package Type (Package Group)'):
            return_vals.update({
                'package_group_data': {
                    'package_type_id': self.get_uom_id_by_name(container_row.get('Package Type (Package Group)'), 'pack'),
                    'quantity': container_row.get('Quantity (Package Group)'),
                    'weight_unit': container_row.get('Weight (Package Group)'),
                    'weight_unit_uom_id': self.get_uom_id_by_name(container_row.get('Weight Unit (Package Group)'), 'weight'),
                    'volume_unit': container_row.get('Volume (Package Group)'),
                    'volume_unit_uom_id': self.get_uom_id_by_name(container_row.get('Volume Unit (Package Group)'), 'volume'),
                    'volumetric_weight': container_row.get('Volumetric Weight (Package Group)'),
                    'weight_volume_unit_uom_id': self.get_uom_id_by_name(container_row.get('Volumetric Weight Unit (Package Group)'), 'weight'),
                    'shipment_id': self.id,
                    'package_mode': 'package',
                    'description': container_row.get('Description (Package Group)'),
                    'id': container_row.get('id'),
                    'net_weight': container_row.get('Net Weight (Package Group)'),
                    'net_weight_unit_uom_id': self.get_uom_id_by_name(container_row.get('Net Weight Unit (Package Group)'), 'weight'),
                },
                'package_group_ids': [],
            })
        return return_vals

    def check_fcl_validations(self, val, row, uom_list):
        upload_file_message = False
        if val:
            if val.get('is_hazardous') and not val.get('haz_class_id'):
                upload_file_message = "Row: {} doesn't contain HAZ class.".format(row + 1)
        if uom_list:
            if not self.check_uom_values(uom_list):
                upload_file_message = "Row: {} Weight/Volume/Volumetric Weight UoM doesn't match.".format(row + 1)
            package_group_data = val.get('package_group_data')
            if package_group_data:
                messages = []
                if not package_group_data.get('weight_unit_uom_id'):
                    messages.append("Weight Unit")
                if not package_group_data.get('volume_unit_uom_id'):
                    messages.append("Volume Unit")
                if not package_group_data.get('weight_volume_unit_uom_id'):
                    messages.append("Weight-Volume Unit")
                if not package_group_data.get('package_type_id'):
                    messages.append("Package Type")
                if int(package_group_data.get('weight_unit') or 0) > 0 and not package_group_data.get('weight_unit_uom_id'):
                    messages.append("Weight UoM")
                if int(package_group_data.get('volume_unit') or 0) > 0 and not package_group_data.get('volume_unit_uom_id'):
                    messages.append("Volume UoM")
                if int(package_group_data.get('volumetric_weight') or 0) > 0 and not package_group_data.get('weight_volume_unit_uom_id'):
                    messages.append("Volumetric Weight UoM")
                upload_file_message = "Row: %s doesn't contain %s." % (row + 1, ','.join(messages)) if messages else False
        return upload_file_message if upload_file_message else False

    def _get_row_data_from_xls(self, worksheet):
        container_columns = self.get_container_template_column_names()
        header_row = [worksheet.cell_value(0, col) for col in range(len(container_columns)) if worksheet.cell_value(0, col)]
        container_row_data = {}
        for row in range(1, worksheet.nrows):
            elm = {}
            for col in range(len(container_columns)):
                value = worksheet.cell_value(row, col)
                header_value = header_row[col]

                # Skip empty cells based on the header
                if not header_value:
                    break

                cell = worksheet.cell(row, col)
                if cell.ctype is xlrd.XL_CELL_NUMBER:
                    is_float = cell.value % 1 != 0.0
                    value = str(cell.value) if is_float else str(int(cell.value))
                elm[header_value] = value
            if elm:
                package_id = int(worksheet.cell_value(row, 100) or '0') if worksheet.ncols >= 100 else 0
                if package_id > 0:
                    elm['id'] = package_id
                container_row_data.update({row: elm})
        return container_row_data

    def _prepare_find_existing_container_line_domain(self, values):
        self.ensure_one()
        return [('shipment_id', '=', self.id),
                ('container_number', '=', False),
                ('container_type_id', '=', values.get('container_type_id')),
                ('weight_unit', '=', values.get('weight_unit')),
                ('weight_unit_uom_id', '=', values.get('weight_unit_uom_id')),
                ('volume_unit', '=', values.get('volume_unit')),
                ('volume_unit_uom_id', '=', values.get('volume_unit_uom_id')),
                ('volumetric_weight', '=', values.get('volumetric_weight')),
                ('is_hazardous', '=', values.get('is_hazardous')),
                ('haz_class_id', '=', values.get('haz_class_id'))]

    def _get_existing_container_line_id(self, values):
        self.ensure_one()
        return self.container_ids.search(self._prepare_find_existing_container_line_domain(values), limit=1)

    def _get_existing_container_number_line_id(self, container_number):
        self.ensure_one()
        existing_records = self.container_ids.filtered(lambda container: container.container_number.container_number == container_number)
        return existing_records and existing_records[0] or existing_records

    def group_container_number_data(self, data):

        def groupby_function(d):
            return d['container_type_id']

        return groupby(sorted(data, key=groupby_function), groupby_function)

    def _upload_container_list_data(self, workbook):
        fully_import = True
        worksheet = workbook.sheet_by_index(0)
        container_row_data = self._get_row_data_from_xls(worksheet)

        ContainerTypeObj = self.env['freight.container.type']
        Package = self.env['freight.house.shipment.package']
        ContainerNumberObj = self.env['freight.master.shipment.container.number']
        container_data = {}
        all_container_numbers = []
        iso_invalid_numbers = []
        all_seal_numbers = []
        skipped_rows = []
        invalid_container_type = []
        without_container_number_rows = []
        container_package_line_uom = {}
        upload_file_message = False
        for row, container in container_row_data.items():
            container_code = container.get('Container Type Code')
            container_number = container.get('Container Number')
            seal_number = container.get('Seal Number')
            if seal_number in all_seal_numbers:
                upload_file_message = 'Row:{} Found duplicate seal number-{} within file.'.format(row + 1, seal_number)
                break
            if seal_number and container_number:
                container_number_id = ContainerNumberObj.search([('name', '=', container_number)], limit=1)
                is_duplicate_seal = ContainerNumberObj._is_duplicate_seal_number(seal_number, container_number_id.id) \
                    if container_number_id else ContainerNumberObj._is_duplicate_seal_number(seal_number)
                if is_duplicate_seal:
                    upload_file_message = 'Row:{} Found duplicate seal number-{} file.'.format(row + 1, seal_number)
                    break
            if container_code:
                container_type_id = ContainerTypeObj.search([('code', '=', container_code)], limit=1)
                if container_type_id:
                    if container_number:
                        if container_number in all_container_numbers or seal_number in all_seal_numbers:
                            repeat_container_vals = container_data[container_number]
                            container_vals = self._prepare_container_vals(container)
                            if repeat_container_vals and repeat_container_vals.get('container_type_id') == container_type_id.id and 'package_group_data' in container_vals:
                                package_group_data = container_vals.pop('package_group_data')
                                if 'package_group_ids' not in repeat_container_vals:
                                    repeat_container_vals['package_group_ids'] = []
                                if 'existing_package_group_ids' not in repeat_container_vals:
                                    repeat_container_vals['package_group_ids'] = []
                                uom_data = '{}_{}_{}'.format(
                                    package_group_data.get('weight_unit_uom_id'), package_group_data.get('volume_unit_uom_id'), package_group_data.get('weight_volume_unit_uom_id'))
                                if container_code not in container_package_line_uom:
                                    container_package_line_uom.update({container_code: [uom_data]})
                                else:
                                    container_package_line_uom[container_code].append(uom_data)
                                if package_group_data.get('id') and Package.browse(int(package_group_data.get('id'))).exists():
                                    repeat_container_vals['existing_package_group_ids'].append(package_group_data)
                                else:
                                    repeat_container_vals['package_group_ids'].append((0, 0, package_group_data))
                                upload_file_message = self.check_fcl_validations(container_vals, row, container_package_line_uom.get(container_code) or [])
                                if upload_file_message:
                                    break
                            else:
                                upload_file_message = self.check_fcl_validations(container_vals, row, container_package_line_uom.get(container_code) or [])
                                if upload_file_message:
                                    break
                                # upload_file_message = 'Row:{} Container-Number: {} | Seal-Number: {} | Package Group: {}'.format(
                                #     row + 1, container_number, seal_number, container_vals.get('package_group_data', None))
                                # skipped_rows.append(upload_file_message)
                                # break
                            if upload_file_message:
                                break
                        else:
                            valid_container_number = self._ISO_validate_container_number(container_number)
                            if valid_container_number:
                                all_container_numbers.append(container_number)
                                if seal_number:
                                    all_seal_numbers.append(seal_number)
                                val = {
                                    'container_type_id': container_type_id.id,
                                    'seal_number': seal_number or False,
                                }
                                val.update(self._prepare_container_vals(container))
                                # if val and val.get('is_hazardous') and not val.get('haz_class_id'):
                                #     upload_file_message = "Row: {} doesn't contain HAZ class.".format(row + 1)
                                #     break
                                if 'existing_package_group_ids' not in val:
                                    val['existing_package_group_ids'] = []
                                if 'package_group_data' in val:
                                    package_group_data = val.pop('package_group_data')
                                    uom_data = '{}_{}_{}'.format(
                                        package_group_data.get('weight_unit_uom_id'), package_group_data.get('volume_unit_uom_id'), package_group_data.get('weight_volume_unit_uom_id'))
                                    if container_code not in container_package_line_uom:
                                        container_package_line_uom.update({container_code: [uom_data]})
                                    else:
                                        container_package_line_uom[container_code].append(uom_data)
                                    # if not self.check_uom_values(container_package_line_uom[container_code]):
                                    #     upload_file_message = "Row: {} Weight/Volume/Volumetric Weight UoM doesn't match or missing.".format(row + 1)
                                    #     break
                                    if package_group_data.get('id') and Package.browse(int(package_group_data.get('id'))).exists():
                                        val['existing_package_group_ids'].append(package_group_data)
                                    else:
                                        val['package_group_ids'].append((0, 0, package_group_data))
                                container_data[container_number] = val
                                upload_file_message = self.check_fcl_validations(val, row, container_package_line_uom.get(container_code) or [])
                                if upload_file_message:
                                    break
                            else:
                                iso_invalid_numbers.append(container_number)
                                upload_file_message = "Row: {} contain ISO Invalid Container Number.".format(row + 1)
                                break
                    else:
                        if not Package.search([('container_type_id', '=', container_type_id.id), ('shipment_id', '=', self.id)], limit=1):
                            val = {
                                'container_type_id': container_type_id.id,
                            }
                            container_vals = self._prepare_container_vals(container)
                            if 'package_group_data' in container_vals:
                                package_group_data = container_vals.get('package_group_data')
                                uom_data = '{}_{}_{}'.format(
                                    package_group_data.get('weight_unit_uom_id'), package_group_data.get('volume_unit_uom_id'), package_group_data.get('weight_volume_unit_uom_id'))
                                if container_code not in container_package_line_uom:
                                    container_package_line_uom.update({container_code: [uom_data]})
                                else:
                                    container_package_line_uom[container_code].append(uom_data)
                            upload_file_message = self.check_fcl_validations(container_vals, row, container_package_line_uom.get(container_code) or [])
                            if upload_file_message:
                                break
                            val.update(container_vals)
                            without_container_number_rows.append(val)
                else:
                    invalid_container_type.append(container_code)
                    upload_file_message = "Row: {} contain Invalid/Missing Container Type.".format(row + 1)
                    break
        if upload_file_message:
            self.upload_file_message = upload_file_message
            return False
        validation_msg = []
        if skipped_rows:
            validation_msg.append('''Skipped row- Please check required missing values:\n - %s''' % (','.join(skipped_rows)))
            fully_import = False
        if invalid_container_type:
            validation_msg.append('''Invalid Container Type:\n - %s''' % (','.join(invalid_container_type)))
            fully_import = False
        if iso_invalid_numbers:
            validation_msg.append('''Invalid Container Number as per ISO 6346 Standard:\n - %s''' % (','.join(iso_invalid_numbers)))
            fully_import = False

        ContainerNumberObj = self.env['freight.master.shipment.container.number']
        # Latest Changes done in fm_container_validation
        # container_number_ids = self.container_ids.mapped('container_number')
        # existing_container_numbers = ContainerNumberObj \
        #     .search([('container_number', 'in', all_container_numbers), ('id', 'not in', container_number_ids.ids),
        #              ('status', '!=', 'unused')])
        # existing_container_numbers = existing_container_numbers.mapped('container_number')
        # if existing_container_numbers:
        #     validation_msg.append('''Container Number Duplicate:\n - %s already exists in system. Please remove it or replace with another number.'''
        #                           % (', '.join(list(set(existing_container_numbers)))))
        #     container_data = {key: value for key, value in container_data.items() if key not in existing_container_numbers}
        #     fully_import = False
        existing_seal_numbers = Package.search([('seal_number', 'in', all_seal_numbers), ('shipment_id', '!=', self.id)])
        existing_seal_numbers = existing_seal_numbers.mapped('seal_number')
        if existing_seal_numbers:
            validation_msg.append('''Seal Number Duplicate in System:\n - %s. Please remove it or replace with another number.'''
                                  % (', '.join(list(set(existing_seal_numbers)))))
            container_data = {key: value for key, value in container_data.items() if value.get('seal_number') not in existing_seal_numbers}
            fully_import = False
        write_vals = []
        for key, value in container_data.items():
            existing_container_number_line_id = self._get_existing_container_number_line_id(key)
            existing_packages = value.pop('existing_package_group_ids')
            for existing_package in existing_packages:
                package = Package.browse(existing_package.pop('id'))
                package.write(existing_package)
            if existing_container_number_line_id:
                existing_container_number_line_id.container_number.write({
                    'container_type_id': value.get('container_type_id'),
                    # 'seal_number': value.pop('seal_number'),
                    # 'customs_seal_number': value.pop('customs_seal_number'),
                })
                existing_container_number_line_id.write(value)
                existing_container_number_line_id._onchange_container_number()
            else:
                existing_container_line_id = self._get_existing_container_line_id(value)
                container_number_id = ContainerNumberObj.search([
                    ('container_number', '=', key), ('container_type_id', '=', value.get('container_type_id')), ('status', '=', 'unused')], limit=1)
                if not container_number_id:
                    container_number_vals = {
                        'container_type_id': value.get('container_type_id'),
                        'container_number': key,
                    }
                    container_number_id = ContainerNumberObj.create(container_number_vals)
                if existing_container_line_id:
                    existing_container_line_id.write({
                        'container_number': container_number_id.id,
                        'seal_number': value.pop('seal_number'),
                        'customs_seal_number': value.pop('customs_seal_number'),
                    })
                    existing_container_line_id._onchange_container_number()
                else:
                    value.update({
                        'container_number': container_number_id.id,
                        'shipment_id': self.id,
                        'seal_number': value.pop('seal_number'),
                        'customs_seal_number': value.pop('customs_seal_number'),
                    })
                    container_id = self.env['freight.house.shipment.package'].new(value)
                    container_id._onchange_container_number()
                    new_val = container_id._convert_to_write(container_id._cache)
                    write_vals.append((0, 0, new_val))
        if without_container_number_rows:
            container_data_rows = []
            grouped_data = self.group_container_number_data(without_container_number_rows)
            for distinct_values, groupby_res in grouped_data:
                result = list(groupby_res)
                if result and result[0].get('package_group_data'):
                    package_group_ids = list(map(lambda data: data.get('package_group_data'), result))
                    result[0]['package_group_ids'] = [(0, 0, package_data) for package_data in package_group_ids]
                container_data_rows.append(result[0])
            for row in container_data_rows:
                data = dict(row)
                for key, value in data.items():
                    if not hasattr(Package, key):
                        del row[key]
                write_vals.append((0, 0, row))
        if write_vals:
            try:
                self.write({
                    'container_ids': write_vals
                })
            except Exception as e:
                _logger.warning(e)
                validation_msg.append('Import Fail: {}'.format(e))
        if validation_msg:
            self.upload_file_message = '\n'.join(validation_msg)
        if fully_import:
            self.upload_file_message = False

    def action_upload_container_list(self, **kwargs):
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
            if attachment and attachment.mimetype not in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel']:
                attachment.unlink()
                self.upload_file_message = 'Only Excel files are accepted.'
            else:
                if attachment.description:
                    self.upload_file_message = attachment.description
                    attachment.unlink()
                else:
                    self.upload_file_message = 'Could not read file properly, Please check file and upload file again!\nContainer Type Code | Container Number | Seal Number | Customs Seal'
            workbook = False
            return True

        try:
            self._upload_container_list_data(workbook)
        except Exception as e:
            _logger.warning(e)
            IrLogging = self.env['ir.logging'].sudo()
            IrLogging.create({
                'name': 'FCL Upload', 'type': 'server', 'dbname': '-', 'level': 'DEBUG',
                'message': e, 'path': 'FCL > Upload ', 'func': 'action_upload_container_list',
                'line': 1
            })
            self.upload_file_message = 'Could not process file properly, Please validate file and upload file again!'
            return True

    def action_clear_upload_file_message(self):
        """
        Remove 'Upload File Message' from the view.
        """
        self.upload_file_message = False
