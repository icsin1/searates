# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    office365_url_verifier_file = fields.Binary()
    office365_url_verifier_filename = fields.Char()


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    office356_url_verify_identifier = fields.Char('Office365 URL Identifier', config_parameter='office356_url_verify_identifier')
    office365_url_verifier_file = fields.Binary(related='company_id.office365_url_verifier_file', readonly=False, string='Office365 URL Verifier File')
    office365_url_verifier_filename = fields.Char(related='company_id.office365_url_verifier_filename', readonly=False, string='Office365 URL Verifier Filename')
