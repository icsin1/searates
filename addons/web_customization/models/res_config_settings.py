# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    view_customization = fields.Selection(related='company_id.view_customization', readonly=False, required=True)
