import logging

from odoo import models

from stdnum.iso6346 import is_valid as is_valid_container_number

_logger = logging.getLogger(__name__)


class FreightHouseShipmentFCL(models.Model):
    _inherit = 'freight.house.shipment'

    def _ISO_validate_container_number(self, container_number):
        return is_valid_container_number(container_number)

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
                                upload_file_message = 'Row:{} Container-Number: {} | Seal-Number: {} | Package Group: {}'.format(
                                    row + 1, container_number, seal_number, container_vals.get('package_group_data', None))
                                skipped_rows.append(upload_file_message)
                                break
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
        container_number_ids = self.container_ids.mapped('container_number').ids
        container_number_ids += self.parent_id.carrier_booking_container_ids.mapped('container_number_ids').ids \
            if self.parent_id and self.parent_id.carrier_booking_container_ids else []
        existing_container_numbers = ContainerNumberObj \
            .search([('container_number', 'in', all_container_numbers), ('id', 'not in', container_number_ids),
                     ('status', '!=', 'unused')])
        existing_container_numbers = existing_container_numbers.mapped('container_number')
        if existing_container_numbers:
            validation_msg.append('''Container Number Duplicate:\n - %s already exists in system. Please remove it or replace with another number.'''
                                  % (', '.join(list(set(existing_container_numbers)))))
            container_data = {key: value for key, value in container_data.items() if key not in existing_container_numbers}
            fully_import = False
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
                if result and result[0].get('package_group_ids'):
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
