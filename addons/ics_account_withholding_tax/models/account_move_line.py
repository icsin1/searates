from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    withholding_tax_line = fields.Boolean(copy=False)
