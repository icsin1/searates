# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    house_package = env['freight.house.shipment.package'].search([])
    if house_package:
        house_package._compute_allow_container_number()
    master_package = env['freight.master.shipment.package'].search([])
    if master_package:
        master_package._compute_allow_container_number()
    containers = env['freight.master.shipment.container.number'].search([])
    if containers:
        containers._compute_status()
