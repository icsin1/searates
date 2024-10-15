from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ics_edi_token = fields.Char(string='Token', related='company_id.ics_edi_token', readonly=False)
    ics_edi_registration_id = fields.Integer(string='Registration ID', related='company_id.ics_edi_registration_id', readonly=False)
