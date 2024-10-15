from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class NotificationSettings(models.Model):
    _name = "notification.settings"
    _description = "Notification Settings"

    model_id = fields.Many2one('ir.model', string='Document Model', ondelete='cascade', required=True)
    field_id = fields.Many2one('ir.model.fields', string='Date Field', ondelete='cascade', domain="[('model_id', '=', model_id), ('ttype', 'in', ['date', 'datetime'])]", required=True)
    title = fields.Char('Title', required=True)
    days = fields.Integer('Days', default=1, help='Notification before Days', required=True)
    snooze_hours = fields.Integer('Snooze Hours', default=4, required=True)
    user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user, required=True)
    active = fields.Boolean(default=True)

    @api.constrains('model_id', 'field_id', 'user_id')
    def check_unique(self):
        for setting in self:
            if setting.sudo().search([
                ('model_id', '=', setting.model_id.id),
                ('field_id', '=', setting.field_id.id),
                ('user_id', '=', setting.user_id.id),
                ('id', '!=', setting.id)
            ]):
                raise ValidationError(_('You can not create notification for same Model and Field'))

    def has_notification(self, model, vals):
        notifications = self.sudo().search([('model_id.model', '=', model)])
        if notifications and set(vals) & set(notifications.mapped('field_id.name')):
            return True
        return False

    def get_field_value(self, record_id):
        self.ensure_one()
        return self.env[self.model_id.model].browse(record_id)[self.field_id.name]

    def get_notifications(self, user_ids, fields=False):
        return self.sudo().search([('user_id', 'in', user_ids), ('field_id.name', 'in', fields)])

    def create_log(self, name=False, action=False):
        Log = self.env['notification.logs']
        for setting in self:
            Log.create({
                'name': name,
                'notification_setting_id': setting.id,
                'user_id': self.env.user.id,
                'action': action
            })
