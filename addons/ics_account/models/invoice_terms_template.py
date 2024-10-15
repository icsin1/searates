# -*- coding: utf-8 -*-

from odoo import fields, models, api


class InvoiceTermsTemplate(models.Model):
    _name = "invoice.terms.template"
    _description = "Invoice Terms Template"

    name = fields.Char(required=True)
    body_html = fields.Html('Content', translate=True, required=True)
