from odoo import models, fields


class ResCountry(models.Model):
    _inherit = 'res.country'

    vat_report_label = fields.Char(string='Vat Report Label', default='VAT')
