# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools import plaintext2html


class WebNotificationManager(models.AbstractModel):
    _name = 'web.notification.manager'
    _description = 'Web Notification Managr'

    def _send_web_notification(self):
        for record, notification in self.get_all_records():
            record._set_notification(notifications=[notification])

    def get_all_records(self):
        from_date = datetime.today()
        to_date = datetime.today() + relativedelta(days=7)

        for notification in self.env['res.users'].sudo().search([]).mapped('notification_setting_ids'):
            if hasattr(self.env[notification.model_id.model], 'message_partner_ids'):
                for record in self.env[notification.model_id.model].search([
                    (notification.field_id.name, '>=', datetime.combine(from_date, time.min)),
                    (notification.field_id.name, '<=', datetime.combine(to_date, time.max)),
                    ('message_partner_ids.user_ids', 'in', notification.user_id.ids)
                ]):
                    yield record, notification


class Base(models.AbstractModel):
    _inherit = "base"

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if getattr(self, 'message_partner_ids', False) and self.env['notification.settings'].has_notification(self._name, vals):
            res.sudo()._set_notification(vals)
        return res

    def write(self, vals):
        res = super().write(vals)
        if getattr(self, 'message_partner_ids', False) and self.env['notification.settings'].has_notification(self._name, vals):
            self.sudo()._set_notification(vals)
        return res

    def _set_notification(self, vals=False, notifications=False):
        self.ensure_one()
        notification_list = []
        for notification in notifications or self.env['notification.settings'].get_notifications(self.message_partner_ids.user_ids.ids, vals and list(vals)):
            notif = self.with_user(notification.user_id).with_context(allowed_company_ids=notification.user_id.company_ids.ids).do_notif_reminder(notification)
            notification_list.append([notification.user_id.partner_id, 'web.notification', [notif]])

        if len(notification_list) > 0:
            self.env['bus.bus']._sendmany(notification_list)

    def _get_message(self, value):
        return f"""
            {self._description} needs action before {fields.Datetime.to_string(value)}
        """

    def do_notif_reminder(self, notification, snooze=False):
        value = notification.get_field_value(self.id)
        if not isinstance(value, datetime):
            value = datetime(value.year, value.month, value.day)

        message = plaintext2html(self._get_message(value))
        if snooze:
            delta = notification.snooze_hours * 60 * 60
        else:
            delta = value - relativedelta(days=notification.days) - fields.Datetime.now()
            delta = delta.seconds + delta.days * 3600 * 24

        return {
            'notification_id': notification.id,
            'res_id': self.id,
            'res_model': self._name,
            'title': f'{self.name} {notification.title or ""}',
            'message': message,
            'timer': delta,
            'notify_at': fields.Datetime.to_string(value),
        }

    @api.model
    def get_next_notif(self, notif=False):
        notification = self.env['notification.settings'].browse(notif['notification_id'])
        if notification.exists():
            notif = self.sudo().do_notif_reminder(notification, snooze=True)
            return self.env['bus.bus'].sudo()._sendone(notification.user_id.partner_id, 'web.notification', [notif])
