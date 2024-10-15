# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    quote = env['shipment.quote'].sudo().search([])
    if quote:
        quote._compute_estimated_margin_percent()
    quote_charges = env['shipment.quote.line'].sudo().search([])
    if quote_charges:
        quote_charges._compute_estimated_margin_percentage()
