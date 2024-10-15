# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    quote = env['shipment.quote'].sudo().search([])
    team = env.ref('fm_sale_crm.team_sales_department').id
    if quote:
        quote.team_id = team
