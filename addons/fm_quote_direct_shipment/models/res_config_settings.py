# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    create_shipment_for = fields.Selection([('house_shipment', 'House Shipment'), ('master_shipment', 'Master Shipment')], string="Create Shipment For", related='company_id.create_shipment_for',
                                           readonly=False)
