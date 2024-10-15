# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for filter in env['web.report.filter'].search([('filter_key', '=', False)]):
        filter._onchange_name()
