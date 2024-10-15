# -*- coding: utf-8 -*-

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    create_shipment_for = fields.Selection([('house_shipment', 'House Shipment'), ('master_shipment', 'Master Shipment')], string="Create Shipment For")
