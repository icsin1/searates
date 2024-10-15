
from odoo import models, fields


class ResBank(models.Model):
    _inherit = 'res.bank'

    bic = fields.Char(string="Swift/BIC Code")
    iban_number = fields.Char(string="IBAN Number", help="International Bank Account Number")
