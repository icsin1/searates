# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    service_job = env['freight.service.job'].sudo().search([])
    if service_job:
        service_job._compute_estimated_margin_percentage()
        service_job._compute_received_margin_percentage()
