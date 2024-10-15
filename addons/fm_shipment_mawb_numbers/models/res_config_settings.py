# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    skip_mawb_validations = fields.Boolean(string="Skip MAWB Validations",
                                           readonly=False,
                                           related='company_id.skip_mawb_validations')
