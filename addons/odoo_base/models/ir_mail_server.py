# -*- coding: utf-8 -*-

from odoo import models, fields


class IrMailServer(models.Model):
    _inherit = "ir.mail_server"

    from_filter = fields.Char(
      "From Filter",
      help='Define for which email address or domain this server can be used.\n'
      'e.g.: "notification@searateserp.com" or "searateserp.com"')

    def _get_test_email_addresses(self):
        email_from, email_to = super()._get_test_email_addresses()
        return email_from, 'noreply@searateserp.com'
