# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for house_shipment in env['freight.house.shipment'].sudo().search([]):
        house_shipment.cal_container_number()
