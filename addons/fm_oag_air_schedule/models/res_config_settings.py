from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    oag_environment = fields.Selection([
        ('sandbox', 'Sandbox'),
        ('production', 'Production')
    ], default='sandbox', string='OAG Environment', config_parameter='fm_oag_air_schedule.oag_environment')

    oag_api_key = fields.Char('OAG API Key', config_parameter='fm_oag_air_schedule.oag_api_key')
