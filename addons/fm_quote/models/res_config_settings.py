# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_quote_routing = fields.Boolean(string="Enable Quote Routing", related='company_id.enable_quote_routing', readonly=False)
    shipment_allow_shipper_consignee_change = fields.Boolean(string="Shipper/Consignee Updation", related='company_id.shipment_allow_shipper_consignee_change', readonly=False)
