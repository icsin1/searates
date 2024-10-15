from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    ics_edi_token = fields.Char()
    ics_edi_registration_id = fields.Integer()
