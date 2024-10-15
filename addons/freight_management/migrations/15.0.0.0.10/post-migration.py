# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    house_shipment = env['freight.house.shipment'].search([
        ('package_ids', '!=', False), ('container_ids', '!=', False), ('state', 'not in', ['hlr_generated'])])
    for rec in house_shipment:
        packaging_mode = 'container' if rec.cargo_type_id and not rec.cargo_type_id.is_package_group else 'package'
        if packaging_mode == 'package':
            rec.container_number = ', '.join(rec.mapped('package_ids.container_number.container_number'))
            container_types = []
            for package in rec.package_ids:
                if package.container_type_id:
                    container_types.append(
                        '[{}] {}'.format(package.container_type_id.code, package.container_type_id.name))
            rec.container_type = ', '.join(container_types)
        else:
            rec.container_number = ', '.join(rec.mapped('container_ids.container_number.container_number'))
            container_types = []
            for container in rec.container_ids:
                if container.container_type_id:
                    container_types.append(
                        '[{}] {}'.format(container.container_type_id.code, container.container_type_id.name))
            rec.container_type = ', '.join(container_types)
