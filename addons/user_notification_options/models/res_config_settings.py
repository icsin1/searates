# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    email_system_notify = fields.Boolean('Enable Email and System Notification Options', config_parameter='user_notification_options.email_system_notify')
