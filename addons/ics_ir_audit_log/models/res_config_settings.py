# -*- coding: utf-8 -*-
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ics_ir_log_history = fields.Integer('Data history (in Days)', config_parameter='ics_ir_audit_log.ics_ir_log_history', default=180)
