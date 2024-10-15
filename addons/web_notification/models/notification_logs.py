from odoo import models, fields


class NotificationLogs(models.Model):
    _name = "notification.logs"
    _description = "Notification Logs"

    name = fields.Char(string='Record name')
    notification_setting_id = fields.Many2one('notification.settings')
    model_id = fields.Char(related='notification_setting_id.model_id.name')
    field_id = fields.Char(related='notification_setting_id.field_id.field_description')
    title = fields.Char(related='notification_setting_id.title')
    action = fields.Selection([
        ('ok', 'OK'),
        ('details', 'Details'),
        ('snooze', 'Snooze'),
        ('show', 'Show'),
    ], default='show')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, required=True)
