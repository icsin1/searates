from odoo import models, fields


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    email_cc = fields.Char('CC', help='CC email address.')

    def get_mail_values(self, res_ids):
        results = super().get_mail_values(res_ids)
        for res_id in res_ids:
            result = results.get(res_id)
            if result:
                result['email_cc'] = self.email_cc or False
        return results
