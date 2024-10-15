# -*- coding: utf-8 -*-

from odoo import models, api


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        thread = super().message_new(msg_dict, custom_values)
        if self.env.context.get('fetchmail_cron_running') and self.env.context.get('default_fetchmail_server_id'):
            fetchmail_server = self.env['fetchmail.server'].browse(self.env.context.get('default_fetchmail_server_id'))

            if fetchmail_server:
                vals = {}
                if getattr(thread, 'company_id', None) is not None and fetchmail_server.company_id:
                    vals.update({'company_id': fetchmail_server.company_id.id})
                vals and thread.write(vals)

        return thread
