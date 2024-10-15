
from odoo import models, fields


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    visible_on_report = fields.Boolean(default=False)
