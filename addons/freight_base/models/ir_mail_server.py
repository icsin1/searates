# -*- coding: utf-8 -*-

from odoo import models, fields


class IrMailServer(models.Model):
    _inherit = "ir.mail_server"

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    def _find_mail_server(self, email_from, mail_servers=None):
        """ If mail server company filter context found,
            filtering provided mail server based on context company or
            getting all server with company added.
        """
        if self.env.context.get('filter_mail_server_company'):
            company_ids = self.env.context.get('filter_mail_server_company', [])
            domain = ['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]
            if mail_servers is None:
                mail_servers = self.sudo().search(domain, order='sequence')
            else:
                mail_servers = mail_servers.filtered_domain(domain)
        return super()._find_mail_server(email_from, mail_servers=mail_servers)


class MailMail(models.Model):
    _inherit = 'mail.mail'

    def _split_by_mail_configuration(self):
        """ Adding context for filtering mail server based on active company if record not found,
            and company on record if record found
        """
        company_ids = [self.env.company.id]
        for mail in self:
            if mail.model and mail.res_id:
                record = self.env[mail.model].sudo().with_context(prefetch_fields=False).browse(mail.res_id)
                if record.exists() and getattr(record, 'company_id', None) is not None:
                    company_ids.append(record.company_id.id)
        self = self.with_context(filter_mail_server_company=company_ids)
        return super()._split_by_mail_configuration()
