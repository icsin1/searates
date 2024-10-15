# -*- coding: utf-8 -*-
import random

from odoo import models, _


class MailBot(models.AbstractModel):
    _inherit = 'mail.bot'

    def _get_answer(self, record, body, values, command=False):
        # onboarding
        odoobot_state = self.env.user.odoobot_state
        if self._is_bot_in_private_channel(record):
            # main flow
            if odoobot_state == 'onboarding_emoji' and self._body_contains_emoji(body):
                self.env.user.odoobot_state = "onboarding_attachement"
                return _("Great! 👍<br/>Now, try to <b>send an attachment</b>, like a picture of your cute dog...")
            elif odoobot_state == 'onboarding_attachement' and values.get("attachment_ids"):
                self.env.user.odoobot_state = "onboarding_command"
                return _("Not a cute dog, but you get it 😊<br/>To access special features, <b>start your sentence with '/'</b>. Try to get help.")
            elif odoobot_state == 'onboarding_command' and command == 'help':
                self.env.user.odoobot_state = "onboarding_ping"
                return _("Wow you are a natural!<br/>Ping someone to grab its attention with @nameoftheuser. <b>Try to ping me using @System</b> in a sentence.")
            elif odoobot_state == 'onboarding_ping' and self._is_bot_pinged(values):
                self.env.user.odoobot_state = "idle"
                return _("Yep, I am here! 🎉 <br/>You finished the tour, you can <b>close this chat window</b>. Enjoy discovering Portal.")
            elif odoobot_state == "idle" and (_('start the tour') in body.lower()):
                self.env.user.odoobot_state = "onboarding_emoji"
                return _("To start, try to send me an emoji :)")
            # easter eggs
            elif odoobot_state == "idle" and body in ['❤️', _('i love you'), _('love')]:
                return _("Aaaaaw that's really cute but, you know, bots don't work that way. You're too human for me! Let's keep it professional ❤️")
            elif odoobot_state == "idle" and (('help' in body) or _('help') in body):
                return _("I'm just a bot... :( May be in future I can talk better with you. ;)")
            elif _('fuck') in body or "fuck" in body:
                return _("That's not nice! I'm a bot but I have feelings too... 💔")
            else:
                #repeat question
                if odoobot_state == 'onboarding_emoji':
                    return _("Not exactly. To continue the tour, send an emoji, <b>type \":)\"</b> and press enter.")
                elif odoobot_state == 'onboarding_attachement':
                    return _("To <b>send an attachment</b>, click the 📎 icon on the right, and select a file.")
                elif odoobot_state == 'onboarding_command':
                    return _("Not sure wat you are doing. Please press / and wait for the propositions. Select \"help\" and press enter")
                elif odoobot_state == 'onboarding_ping':
                    return _("Sorry, I am not listening. To get someone's attention, <b>ping him</b>. Write \"@ionbot\" and select me.")
                return random.choice([
                    _("I'm not smart enough to answer your question.<br/>To follow my guide, ask") + ": <b>"+_('start the tour') + "</b>",
                    _("Hmmm..."),
                    _("Are you testing me ?  o_o "),
                    _("I'm afraid I don't understand. Sorry!"),
                    _("Sorry I'm sleepy. Or not! Maybe I'm just trying to hide my unawareness of human language...<br/>I can show you features if you write")+ ": '<b>"+_('start the tour')+"</b>'.",
                ])
        elif self._is_bot_pinged(values):
            return random.choice([_("Yep, System is in the place!"), _("Pong.")])
        return False


class MailTemplate(models.Model):
    _inherit = "mail.template"

    def send_mail(self, *args, **kwargs):
        kwargs.update({'force_send': False})
        return super().send_mail(*args, **kwargs)


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _notify_record_by_email(self, *args, **kwargs):
        kwargs.update({'force_send': False})
        return super()._notify_record_by_email(*args, **kwargs)
