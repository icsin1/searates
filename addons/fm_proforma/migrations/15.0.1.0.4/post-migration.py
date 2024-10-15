# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for pro_forma in env['pro.forma.invoice'].sudo().search([('house_shipment_id', '!=', False)]):
        pro_forma.write({
            'charge_house_shipment_ids': [(6, 0, pro_forma.house_shipment_id.ids)],
        })
