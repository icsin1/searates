from odoo import models, api


class MailComposerMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.model
    def _action_send_mail(self, auto_commit=False):
        # Call the original _action_send_mail function from the parent class using super()
        result = super(MailComposerMessage, self)._action_send_mail(auto_commit=auto_commit)
        template_id = self.env.context.get('default_template_id')
        if self.env.context.get('send_proforma', False):
            if template_id == self.env.ref('fm_proforma.pro_forma_invoice_email_template').id:
                self.env['pro.forma.invoice'].browse(self.env.context.get('default_res_id')).state = 'sent' 
        return result
