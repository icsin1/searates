from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_fm_oag_air_schedule = fields.Boolean(default=False, string='OAG Air Schedule')
