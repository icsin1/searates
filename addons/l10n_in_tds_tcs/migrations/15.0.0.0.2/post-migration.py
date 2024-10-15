# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for tax in env['account.tax'].sudo().search([]):
        tax.onchange_tax_group_id()
