# -*- coding: utf-8 -*-

from odoo import api, models, _


class Channel(models.Model):
    _inherit = 'mail.channel'

    @api.model
    def init_odoobot(self):
        if self.env.user.odoobot_state == 'not_initialized':
            partner = self.env.user.partner_id
            odoobot_id = self.env['ir.model.data'].xmlid_to_res_id("base.partner_root")
            channel = self.with_context(mail_create_nosubscribe=True).create({
                'channel_partner_ids': [(4, partner.id), (4, odoobot_id)],
                'public': 'private',
                'channel_type': 'chat',
                'email_send': False,
                'name': 'iONBot'
            })
            message = _("Hello,<br/>Portal's chat helps employees collaborate efficiently. I'm here to help you discover its features.<br/><b>Try to send me an emoji :)</b>")
            channel.sudo().message_post(body=message, author_id=odoobot_id, message_type="comment", subtype="mail.mt_comment")
            self.env.user.odoobot_state = 'onboarding_emoji'
            return channel
