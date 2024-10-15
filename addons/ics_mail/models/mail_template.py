from odoo import models


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    def generate_recipients(self, results, res_ids):
        """ Email CC Patch

            As mail template auto add email_cc to recipients and we have already introduced
            email cc field so skipping to auto calculate and new partners are created.

            Now, it will add to email cc as raw value instead of calculating the partners
            See @mail/models/mail_template.py:generate_recipients()
        """
        email_ccs = {}
        for res_id in res_ids:
            values = results.get(res_id)
            if values.get('email_cc'):
                email_ccs[res_id] = values.get('email_cc')
                values['email_cc'] = False
        results = super().generate_recipients(results, res_ids)

        for res_id, email_cc in email_ccs.items():
            results[res_id].update({'email_cc': email_cc})

        return results
