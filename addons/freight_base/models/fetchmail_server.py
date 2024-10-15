# -*- coding: utf-8 -*-

from odoo import models, fields


class FetchmailServer(models.Model):
    _inherit = "fetchmail.server"

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
