# -*- coding: utf-8 -*-
from odoo import models


class CustomBaseModel(models.BaseModel):
    _inherit = 'base'

    def notify_user(self, title, message, message_type='default', sticky=False):
        '''Method to Update User with the Bus-channel notification
            message_type (String): Message type - 'info', 'success', 'warning', 'danger' or 'default'
            title (String): Title for the notification message
            message (String): Message to be display on after title
            sticky (Boolean): Notification message will be stick to the screen until user closes
        '''
        bus_message = {
            "title": title,
            "type": message_type,
            "message": message,
            "sticky": sticky,
            "warning": True,
        }
        self.env['bus.bus']._sendone(self.env.user.partner_id, 'web.confirmation', [bus_message])
