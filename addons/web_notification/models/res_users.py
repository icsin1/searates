from datetime import datetime
from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    notification_setting_ids = fields.One2many('notification.settings', 'user_id', string='Notifications')
    notification_log_ids = fields.One2many('notification.logs', 'user_id', string='Notifications')


class Partner(models.Model):
    _inherit = 'res.partner'

    web_last_notif_ack = fields.Datetime('Last notification marked as read', default=fields.Datetime.now)

    @api.model
    def _set_web_last_notif_ack(self):
        partner = self.env['res.users'].browse(self.env.context.get('uid', self.env.uid)).partner_id
        partner.write({'web_last_notif_ack': datetime.now()})
