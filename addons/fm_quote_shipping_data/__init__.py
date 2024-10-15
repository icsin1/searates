# -*- coding: utf-8 -*-
from . import models

from odoo import api, SUPERUSER_ID


def _shipping_data_post_init(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for record in env['shipment.quote'].sudo().search([('quote_for', '=', 'shipment')]):
        record.create_shipping_line_and_agent()
