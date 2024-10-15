# -*- coding: utf-8 -*-

from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    notification_type = fields.Selection([
        ('email', 'Handle by Emails'),
        ('inbox', 'Handle in System')
    ], default='email', help="Policy on how to handle Chatter notifications:\n"
             "- Handle by Emails: notifications are sent to your email address\n"
             "- Handle in System: notifications appear in your System Inbox")
    odoobot_state = fields.Selection(string="Bot Status")
