from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    ms_mail_matched = fields.Boolean(compute='_compute_ms_mail_matched')
    ms_smtp_configured = fields.Boolean(compute='_compute_ms_mail_matched')

    @api.depends('email')
    def _compute_ms_mail_matched(self):
        mail_catchall_domain = self.env['ir.config_parameter'].sudo().get_param('mail.catchall.domain', False)
        for rec in self:
            MailServer = self.env['ir.mail_server'].sudo()
            mail_server = MailServer.search([('smtp_user', '=', self.email)])
            rec.ms_mail_matched = rec.email.endswith(mail_catchall_domain)
            rec.ms_smtp_configured = mail_server and mail_server.microsoft_outlook_refresh_token or False

    def action_authorize_ms_outlook(self):
        self.ensure_one()
        MailServer = self.env['ir.mail_server'].sudo()
        mail_server = MailServer.search([('smtp_user', '=', self.email)])
        values = {
            'name': self.email,
            'from_filter': self.email,
            'use_microsoft_outlook_service': True,
            'smtp_user': self.email,
            'smtp_host': 'smtp.outlook.com',
            'smtp_encryption': 'starttls',
            'smtp_port': 587
        }
        if not mail_server:
            mail_server = MailServer.create(values)
        else:
            mail_server.write(values)
        mail_server._onchange_use_microsoft_outlook_service()
        return mail_server.open_microsoft_outlook_uri()

    def action_remove_ms_outlook(self):
        MailServer = self.env['ir.mail_server'].sudo()
        mail_server = MailServer.search([('smtp_user', '=', self.email)])
        mail_server.unlink()
