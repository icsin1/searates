# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_fm_service_job_proforma = fields.Boolean(string="Pro-Forma Invoice on Service Job")
