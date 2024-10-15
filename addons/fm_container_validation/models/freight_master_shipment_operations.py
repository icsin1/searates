
from odoo import models,  _
import io
import base64
import logging

from stdnum.iso6346 import is_valid as is_valid_container_number

from odoo.tools.misc import xlsxwriter

_logger = logging.getLogger(__name__)


class FreightMasterShipmentOperations(models.Model):
    _inherit = 'freight.master.shipment'

    def _ISO_validate_container_number(self, container_number):
        return is_valid_container_number(container_number)

    def _upload_container_list_data(self, workbook):
        fully_import = True
        worksheet = workbook.sheet_by_index(0)
        container_row_data = self._get_row_data_from_xls(worksheet)
        ContainerTypeObj = self.env['freight.container.type']
        ContainerModeObj = self.env['container.service.mode']
        container_data = {}
        all_container_numbers = []
        all_seal_numbers = []
        skipped_rows = []
        iso_invalid_numbers = []
        without_container_number_rows = []
        invalid_container_type = []
        invalid_container_mode = []
        for container in container_row_data:
            container_code = container.get('Container Type Code')
            container_mode = container.get('Container Mode')
            container_number = container.get('Container Number')
            seal_number = container.get('Seal Number')
            if container_code and container_mode:
                container_type_id = ContainerTypeObj.search([('code', '=', container_code)], limit=1)
                container_mode_id = ContainerModeObj.search([('code', '=', container_mode)], limit=1)
                if container_type_id and container_mode_id:
                    if container_number:
                        if container_number in all_container_numbers or seal_number in all_seal_numbers:
                            skipped_rows.append('Container-Number: {} | Seal-Number: {}'.format(container_number, seal_number))
                        else:
                            valid_container_number = self._ISO_validate_container_number(container_number)
                            if valid_container_number:
                                all_container_numbers.append(container_number)
                                if seal_number:
                                    all_seal_numbers.append(seal_number)
                                val = {
                                    'container_type_id': container_type_id.id,
                                    'container_mode_id': container_mode_id.id,
                                    'seal_number': seal_number or False,
                                }
                                val.update(self._prepare_container_vals(container))
                                container_data[container_number] = val
                            else:
                                iso_invalid_numbers.append(container_number)
                    else:
                        val = {
                            'container_type_id': container_type_id.id,
                            'container_mode_id': container_mode_id.id,
                        }
                        val.update(self._prepare_container_vals(container))
                        without_container_number_rows.append(val)
                else:
                    if not container_type_id:
                        invalid_container_type.append(container_code)
                    if not container_mode_id:
                        invalid_container_mode.append(container_mode)

        validation_msg = []
        if skipped_rows:
            validation_msg.append('''Skipped row because of Duplicate Container Number within file:\n - %s''' % (','.join(skipped_rows)))
            fully_import = False
        if invalid_container_type:
            validation_msg.append('''Invalid Container Type:\n - %s''' % (','.join(invalid_container_type)))
            fully_import = False
        if invalid_container_mode:
            validation_msg.append('''Invalid Container Mode:\n - %s''' % (','.join(invalid_container_mode)))
            fully_import = False
        if iso_invalid_numbers:
            validation_msg.append('''Invalid Container Number as per ISO 6346 Standard:\n - %s''' % (','.join(iso_invalid_numbers)))
            fully_import = False

        ContainerNumberObj = self.env['freight.master.shipment.container.number']
        container_number_ids = self.carrier_booking_container_ids.mapped('container_number_ids')
        existing_container_numbers = ContainerNumberObj \
            .search([('container_number', 'in', all_container_numbers), ('id', 'not in', container_number_ids.ids)])
        existing_container_numbers = existing_container_numbers.mapped('container_number')
        if existing_container_numbers:
            validation_msg.append(
                '''Container Number Duplicate:\n - %s already exists in system. Please remove it or replace with another number.'''
                % (', '.join(list(set(existing_container_numbers)))))
            container_data = {key: value for key, value in container_data.items() if
                              key not in existing_container_numbers}
            fully_import = False
        existing_seal_numbers = ContainerNumberObj \
            .search([('seal_number', 'in', all_seal_numbers), ('id', 'not in', container_number_ids.ids)])
        existing_seal_numbers = existing_seal_numbers.mapped('seal_number')
        if existing_seal_numbers:
            validation_msg.append(
                '''Seal Number Duplicate in System:\n - %s. Please remove it or replace with another number.'''
                % (', '.join(list(set(existing_seal_numbers)))))
            container_data = {key: value for key, value in container_data.items() if
                              value.get('seal_number') not in existing_seal_numbers}
            fully_import = False
        write_vals = []
        Container = self.env['freight.master.shipment.carrier.container']
        new_rows = []
        update_rows = {}
        for key, value in container_data.items():
            container_exist = self.get_ext_carrier_container(value.get('container_type_id'),
                                                             value.get('container_mode_id'))
            container_number_create_vals = {
                'container_type_id': value.get('container_type_id'),
                'container_number': key,
            }
            container_number_write_vals = {
                'seal_number': value.pop('seal_number') or False,
                'customs_seal_number': value.pop('customs_seal_number') or False,
            }
            # container_number_id = ContainerNumberObj.create(container_number_create_vals + container_number_write_vals)
            for k, val in value.items():
                if not hasattr(Container, k):
                    del value[k]
            if container_exist:
                container_number_exist = container_exist.mapped('container_number_ids').filtered(lambda con: con.container_number == key)
                container_number_exist = container_number_exist and container_number_exist[0]
                row_exist = update_rows.get(container_exist.id)
                if row_exist:
                    if container_number_exist:
                        container_number_ids = row_exist.get('container_number_ids', [])
                        row_exist.update(container_number_ids=container_number_ids + [(1, container_number_exist.id, container_number_write_vals)])
                    else:
                        row_exist.update(container_count=row_exist.get('container_count') + 1)
                else:
                    if container_number_exist:
                        value.update(container_number_ids=[(1, container_number_exist.id, container_number_write_vals)])
                    else:
                        value.update(container_count=len(container_exist.container_number_ids) + 1)
                    update_rows[container_exist.id] = value
                if not container_number_exist:
                    container_number_create_vals.update(container_number_write_vals)
                    container_number_create_vals.update({'container_line_id': container_exist.id})
                    ContainerNumberObj.create(container_number_create_vals)
            else:
                row_exist = list(filter(
                    lambda r: r.get('container_type_id') == value.get('container_type_id') and r.get(
                        'container_mode_id') == value.get('container_mode_id'), new_rows))
                if row_exist:
                    row_exist[0].update({
                        'container_count': row_exist[0].get('container_count') + 1,
                    })
                    if 'container_number_ids' in row_exist[0] and isinstance(row_exist[0].get('container_number_ids'), list):
                        container_number_create_vals.update(container_number_write_vals)
                        container_number_id = ContainerNumberObj.create(container_number_create_vals)
                        row_exist[0]['container_number_ids'].append((4, container_number_id.id))
                else:
                    container_number_create_vals.update(container_number_write_vals)
                    container_number_id = ContainerNumberObj.create(container_number_create_vals)
                    value.update({
                        'container_count': 1,
                        'container_number_ids': [(4, container_number_id.id)],
                    })
                    new_rows.append(value)
        for row in without_container_number_rows:
            data = dict(row)
            container_exist = self.get_ext_carrier_container(data.get('container_type_id'), data.get('container_mode_id'))
            for key, value in data.items():
                if not hasattr(Container, key):
                    del row[key]
            if container_exist:
                row_exist = update_rows.get(container_exist.id)
                if not row_exist:
                    update_rows[container_exist.id] = row
            else:
                row_exist = list(filter(lambda r: r.get('container_type_id') == row.get('container_type_id') and r.get('container_mode_id') == row.get('container_mode_id'), new_rows))
                if not row_exist:
                    new_rows.append(row)
        if new_rows:
            write_vals += [(0, 0, r) for r in new_rows]
        if update_rows:
            write_vals += [(1, k, r) for k, r in update_rows.items()]
        if write_vals:
            try:
                self.write({
                    'carrier_booking_container_ids': write_vals
                })
            except Exception as e:
                _logger.warning(e)
                validation_msg.append(e)
        if validation_msg:
            self.upload_file_message = '\n'.join(validation_msg)
        if fully_import:
            self.upload_file_message = False

    def xls_decimal_data_validation(self):
        return {
            'validate': 'decimal',
            'criteria': '>=',
            'value': 0,
            'error_message': 'Only numeric values are allowed'
        }

    def get_required_columns(self):
        """Add field names if it needs to be required in Container xls"""
        return ['Container Type Code', 'Container Mode']

    def get_container_template_column_names(self):
        return ['Container Type Code', 'Container Mode', 'Container Number', 'Seal Number', 'Customs Seal',
                'Weight', 'Weight Unit', 'Volume', 'Volume Unit', 'Volumetric Weight', 'Volumetric Weight Unit',
                'Is HAZ', 'UN#']

    def action_download_container_numbers_template(self):
        self.ensure_one()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()
        hidden_worksheet = workbook.add_worksheet('DataValidation')

        heading_style = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '12px', 'border': 1})
        heading_required_style = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '12px', 'border': 1, 'bg_color': '#D2D2FF'})
        body_style = workbook.add_format({'font_size': '12px', 'border': 1})

        heading_col = 0
        for column_name in self.get_container_template_column_names():
            style = heading_style
            if column_name in self.get_required_columns():
                style = heading_required_style
            worksheet.write(0, heading_col, column_name, style)
            worksheet.set_column(0, heading_col, 30)
            heading_col += 1

        # Container Type Data
        container_type_data = self.env['freight.container.type'].search([]).mapped('code')
        hidden_worksheet.write_column('M2', container_type_data)
        # worksheet.set_column('M:XFD', None, None, {'hidden': 1})

        # Container Model Data
        container_mode_data = self.env['container.service.mode'].search([]).mapped('code')
        hidden_worksheet.write_column('N2', container_mode_data)
        # worksheet.set_column('N:XFD', None, None, {'hidden': 1})

        # Weight UOM DropDown
        weight_uom_data = self.env['uom.uom'].search(
            [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)]).mapped('name')
        hidden_worksheet.write_column('O2', weight_uom_data)
        # worksheet.set_column('O:XFD', None, None, {'hidden': 1})

        # Volume UOM DropDown
        volume_uom_data = self.env['uom.uom'].search(
            [('category_id', '=', self.env.ref('uom.product_uom_categ_vol').id)]).mapped('name')
        hidden_worksheet.write_column('P2', volume_uom_data)
        # worksheet.set_column('P:XFD', None, None, {'hidden': 1})

        # data validations
        container_type_rows = "A2:A200"
        container_type_source_column = "='datavalidation'!$M$2:$M${}".format(len(container_type_data) + 1)
        container_type_value_rule = {
            'validate': 'list',
            'source': container_type_source_column,
            'input_title': 'Container Type',
            'input_message': _('Select a container type from the list'),
        }
        worksheet.data_validation(container_type_rows, container_type_value_rule)

        container_mode_rows = "B2:B200"
        container_mode_source_column = "='datavalidation'!$N$2:$N${}".format(len(container_mode_data) + 1)
        container_mode_value_rule = {
            'validate': 'list',
            'source': container_mode_source_column,
            'input_title': 'Container Mode',
            'input_message': _('Select a container mode from the list'),
        }
        worksheet.data_validation(container_mode_rows, container_mode_value_rule)

        worksheet.data_validation("F2:F200", self.xls_decimal_data_validation())
        weight_unit_uom_rows = "G2:G200"
        weight_unit_uom_column = "='datavalidation'!$O$2:$O${}".format(len(weight_uom_data) + 1)
        weight_unit_value_rule = {
            'validate': 'list',
            'source': weight_unit_uom_column,
            'input_title': 'Weight Unit UOM',
            'input_message': _('Select a weight unit from the list'),
        }
        worksheet.data_validation(weight_unit_uom_rows, weight_unit_value_rule)

        worksheet.data_validation("H2:H200", self.xls_decimal_data_validation())
        volume_unit_uom_rows = "I2:I200"
        volume_unit_uom_column = "='datavalidation'!$P$2:$P${}".format(len(volume_uom_data) + 1)
        volume_unit_value_rule = {
            'validate': 'list',
            'source': volume_unit_uom_column,
            'input_title': 'Volume Unit',
            'input_message': _('Select a volume unit from the list'),
        }
        worksheet.data_validation(volume_unit_uom_rows, volume_unit_value_rule)

        worksheet.data_validation("J2:J200", self.xls_decimal_data_validation())
        weight_unit_uom_rows = "K2:K200"
        weight_unit_uom_column = "='datavalidation'!$O$2:$O${}".format(len(weight_uom_data) + 1)
        weight_unit_value_rule = {
            'validate': 'list',
            'source': weight_unit_uom_column,
            'input_title': 'Volumetric Weight Unit',
            'input_message': _('Select a volumetric weight unit from the list'),
        }
        worksheet.data_validation(weight_unit_uom_rows, weight_unit_value_rule)

        # auto suggestion for container type code
        # data validations
        container_type_rows = "A2:A200"
        container_type_value_rule = {
            'validate': 'list',
            'source': container_type_source_column,
            'input_title': 'Container Type',
            'input_message': _('Select a container type from the list'),
        }
        worksheet.data_validation(container_type_rows, container_type_value_rule)

        col = 0
        row = 1

        for record in self.carrier_booking_container_ids:
            rec_container_numbers = record.container_number_ids
            container_number_len = len(rec_container_numbers)
            for idx, cntr_code in enumerate([record.container_type_id.code] * record.container_count):
                worksheet.write(row, col, cntr_code or '', body_style)  # A
                worksheet.write(row, col + 1, record.container_mode_id.code or '', body_style)  # B
                cntr_number = rec_container_numbers[idx].container_number or '' if container_number_len > idx else ''
                worksheet.write(row, col + 2, cntr_number or '', body_style)  # C
                act_seal_number = rec_container_numbers[idx].seal_number or '' if container_number_len > idx else ''
                worksheet.write(row, col + 3, act_seal_number or '', body_style)  # D
                cust_seal_number = rec_container_numbers[idx].customs_seal_number or '' if container_number_len > idx else ''
                worksheet.write(row, col + 4, cust_seal_number or '', body_style)  # E
                worksheet.write(row, col + 5, record.weight_unit, body_style)  # F
                worksheet.write(row, col + 6, record.weight_unit_uom_id.name or '', body_style)  # G
                worksheet.write(row, col + 7, record.volume_unit, body_style)  # H
                worksheet.write(row, col + 8, record.volume_unit_uom_id.name or '', body_style)  # I
                worksheet.write(row, col + 9, record.volumetric_weight, body_style)  # J
                worksheet.write(row, col + 10, record.weight_volume_unit_uom_id.name or '', body_style)  # K
                worksheet.write_boolean(row, col + 11, record.is_hazardous, body_style)  # L
                worksheet.write(row, col + 12, record.is_hazardous and record.un_code or '', body_style)  # M
                row += 1
        hidden_worksheet.hide()
        workbook.close()

        file_name = '%s-ContainerList.xlsx' % (self.name.replace('/', '-'))
        xlsx_base64 = base64.b64encode(output.getvalue())

        # FIXME: Do Later, Use direct header instead of field on model to store file
        self.write({'container_document_file_name': file_name, 'container_number_list_file': xlsx_base64})
        url = '/web/content/%s/%s/%s/%s' % (self._name, self.id, 'container_number_list_file', file_name.replace(' ', ''))
        return {'type': 'ir.actions.act_url', 'url': url}
