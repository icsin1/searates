from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_fm_inttra_sailing_schedule = fields.Boolean(default=False)
