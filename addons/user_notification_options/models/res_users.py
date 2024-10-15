from odoo import models, fields, api


class Users(models.Model):
    _inherit = 'res.users'

    @api.model
    def _selection_notify_list(self):
        notify_check = self.env['ir.config_parameter'].sudo().get_param('user_notification_options.email_system_notify')
        if notify_check:
            return [('email', 'Handle by Emails'), ('inbox', 'Handle in System'), ('both', 'Handle by Emails and in System')]
        else:
            return [('email', 'Handle by Emails'), ('inbox', 'Handle in System')]

    notification_type = fields.Selection(selection=_selection_notify_list, required=True, default='email')

