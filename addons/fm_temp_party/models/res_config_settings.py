# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_temp_party = fields.Boolean(string="Enable Temporary Party", related='company_id.enable_temp_party', readonly=False)
