# -*- coding: utf-8 -*-
import pytz
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    query = "UPDATE res_company set code =substr(name, 1, 4)"
    cr.execute(query)

    company = env['res.company'].search([('partner_id.country_id', '!=', False)])
    for rec in company:
        tz = pytz.country_timezones[rec.country_id.code][0]
        if tz:
            rec.tz = tz
