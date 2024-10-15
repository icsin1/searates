from odoo import models


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _notify_email_recipient_values(self, recipient_ids):
        """ Overriding method if requested as grouped email where
            recipients will be grouped as below
                Customer: All customers will be grouped together sent one single email
                Internal Users: Internal User will get individual emails as links are there
        """
        ICP = self.env['ir.config_parameter'].sudo()
        if ICP.get_param('ics_mail.outgoing_email_mode', 'standard') == 'grouped_email':
            partners = self.env['res.partner'].sudo().browse(recipient_ids)
            return {
                'email_to': ', '.join(partners.filtered(lambda partner: partner.email).mapped('email_formatted')),
                'recipient_ids': []
            }
        return super()._notify_email_recipient_values(recipient_ids)

    def _notify_by_email_add_values(self, base_mail_values):
        base_mail_values = super()._notify_by_email_add_values(base_mail_values)
        mail_message = self.env['mail.message'].browse(base_mail_values.get('mail_message_id'))
        if mail_message and mail_message.email_cc:
            base_mail_values['email_cc'] = mail_message.email_cc
        return base_mail_values
