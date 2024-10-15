# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_ics_ir_audit_log = fields.Boolean(string="Audit Log")
