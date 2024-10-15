# -*- coding: utf-8 -*-

import odoo.http as http

from odoo.http import request
from odoo.tools.misc import get_lang


class Controller(http.Controller):

    @http.route('/web_notification/notify_ack', type='json', auth="user")
    def notify_ack(self, notif):
        self.create_log(notif, 'ok')
        return request.env['res.partner'].sudo()._set_web_last_notif_ack()

    @http.route('/web_notification/notify_show', type='json', auth="user")
    def notify_show(self, notif):
        self.create_log(notif, 'show')

    @http.route('/web_notification/notify_details', type='json', auth="user")
    def notify_notify_details(self, notif):
        self.create_log(notif, 'details')

    @http.route('/web_notification/notify_snooze', type='json', auth="user")
    def notify_snooze(self, notif):
        self.create_log(notif, 'snooze')
        record = request.env[notif['res_model']].sudo().browse(notif['res_id'])
        if record.exists():
            return record.get_next_notif(notif=notif)

    def create_log(self, notif, action):
        notification = request.env['notification.settings'].sudo().browse(notif['notification_id'])
        record = request.env[notif['res_model']].sudo().browse(notif['res_id'])
        if notification.exists() and record.exists():
            notification.create_log(name=record.display_name, action=action)
