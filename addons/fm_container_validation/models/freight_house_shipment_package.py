from odoo import models, api, _
from odoo.exceptions import ValidationError


class FreightHouseShipmentPackage(models.Model):
    _inherit = 'freight.house.shipment.package'

    @api.constrains('container_number')
    def _check_container_number_unique(self):
        # Part BL Validations
        for package in self.filtered(lambda pack: pack.container_number and not pack.shipment_id.cargo_is_package_group):
            if not package.shipment_id.is_part_bl and not package.is_unique_container_number():
                raise ValidationError(_('Container number {} is already in use with other House shipment.').format(package.container_number.name))
            if package.shipment_id.is_part_bl and package.is_duplicate_part_bl_container():
                raise ValidationError(_('Part BL Container number {} is already in use with other House shipment.').format(package.container_number.name))
            if not package.shipment_id.is_part_bl and not package.is_container_non_part_bl():
                raise ValidationError(_('Can not add part BL container in non-part BL shipment.'))
            if package.shipment_id.is_part_bl and package.is_container_non_part_bl():
                raise ValidationError(_('Can not add non-part BL container in part BL shipment.'))
            if package.shipment_id.is_part_bl and (package.shipment_id.mode_type != 'sea' or package.shipment_id.shipment_type != 'EXP'):
                raise ValidationError(_('Can not add Part BL container in other than Sea Freight Export Shipment.'))

    def is_unique_container_number(self):
        self.ensure_one()
        if not self.container_number:
            return True

        return self.search_count([
            ('container_number.container_number', '=', self.container_number.container_number),
            ('shipment_id.state', 'not in', ('cancelled', 'completed'))
        ]) <= 1

    def is_duplicate_part_bl_container(self):
        self.ensure_one()
        if not self.container_number:
            return False

        return self.search_count([
            ('is_part_bl', '=', True),
            ('shipment_id', '!=', self.shipment_id.id),
            ('container_number.container_number', '=', self.container_number.container_number),
            ('shipment_id.state', 'not in', ('cancelled', 'completed'))
        ]) > 0

    def is_container_non_part_bl(self):
        self.ensure_one()
        if not self.container_number:
            return False
        if self.container_number and not self.container_number.is_part_bl:
            return True
        else:
            return False

    @api.depends('shipment_id', 'container_type_id')
    def _compute_allow_container_number(self):
        for rec in self:
            containers = rec.shipment_id.parent_id.carrier_booking_container_ids
            container_number_ids = self.env['freight.master.shipment.container.number']
            if rec.package_mode == 'container':
                containers = containers.filtered_domain([('container_type_id', '=', rec.container_type_id.id)])
                container_number_domain = [
                '&', '&',
                ('container_type_id', '=', rec.container_type_id.id), ('status', '=', 'unused'),
                '|', ('house_shipment_package_ids', '=', False),
                ('house_shipment_package_ids.shipment_id.state', 'in', ['completed', 'cancelled'])
            ]
            else:
                if rec.shipment_id.cargo_type_id.code == 'LCL':
                    container_number_domain = [('container_type_id', '=', rec.container_type_id.id), ('status', '=', 'unused')]
                else:
                    container_number_domain = [
                    '|', ('house_shipment_package_ids.shipment_id', 'in', rec.shipment_id.ids),
                    '&', ('house_shipment_package_ids', '=', False),
                    ('status', '=', 'unused')
                ]
            if not rec.shipment_id.is_part_bl:
                container_number_domain.append(('is_part_bl', '=', False))
            container_number_ids = container_number_ids.search(container_number_domain)
            container_number_ids |= containers.container_number_ids
            if rec.shipment_id.is_part_bl and rec.shipment_id.container_ids.mapped('container_number'):
                container_number_ids |= rec.shipment_id.container_ids.mapped('container_number')
            rec.allow_container_number_ids = [(6, False, container_number_ids.ids)]

