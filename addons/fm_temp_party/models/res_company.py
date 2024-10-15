# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    enable_temp_party = fields.Boolean(string="Enable Temporary Party", readonly=False)
