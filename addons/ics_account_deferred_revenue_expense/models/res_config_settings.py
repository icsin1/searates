# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Module to manage Fixed Assets Management in accounting
    module_ics_fixed_assets_management = fields.Boolean(default=False)
