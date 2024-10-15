# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ics_outgoing_email_mode = fields.Selection([
        ('standard', 'Standard'),
        ('grouped_email', 'Group by Audience')
    ], config_parameter='ics_mail.outgoing_email_mode', default='standard')
