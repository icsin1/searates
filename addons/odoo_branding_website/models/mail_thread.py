# -*- coding: utf-8 -*-

from odoo import models


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _message_auto_subscribe_notify(self, partner_ids, template):
        if not self.env.context.get('update_subject'):
            self = self.with_context(update_subject=True)
        return super(MailThread, self)._message_auto_subscribe_notify(partner_ids, template)

    def message_notify(self, subject=False, **kwargs):
        if self.env.context.get('update_subject'):
            if isinstance(self.env.context['update_subject'], str):
                subject = self.env.context['update_subject']
            else:
                subject = '%s, assigned by %s' % (subject, self.env.user.name)
        return super(MailThread, self).message_notify(subject=subject, **kwargs)

    def _track_changes(self, field_to_track, message=False):
        if not message and self.message_ids:
            message_id = field_to_track.message_post(body=f'<strong>{ self._description }:</strong> { self.display_name }').id
            trackings = self.env['mail.tracking.value'].sudo().search([('mail_message_id', '=', self.message_ids[0].id)])
            for tracking in trackings:
                tracking.copy({'mail_message_id': message_id})
        else:
            field_to_track.message_post(body=f'<strong>{ self._description }:</strong> { self.display_name } { message }')
