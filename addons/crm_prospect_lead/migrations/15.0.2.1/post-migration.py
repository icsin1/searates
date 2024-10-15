# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    lead = env['crm.prospect.lead'].sudo().search([])
    oppurtunity = env['crm.prospect.opportunity'].sudo().search([])
    team = env.ref('fm_sale_crm.team_sales_department').id
    if oppurtunity:
        oppurtunity.team_id = team
    if lead:
        lead.team_id = team
