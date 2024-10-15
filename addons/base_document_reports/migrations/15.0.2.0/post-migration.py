# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for record in env['docx.template'].sudo().search([]):
        record._create_or_update_report_action()
