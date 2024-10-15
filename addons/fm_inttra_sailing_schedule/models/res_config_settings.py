from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    inttra_environment = fields.Selection([
        ('sandbox', 'Sandbox'),
        ('production', 'Production')
    ], default='sandbox', string='INTTRA Environment', config_parameter='fm_inttra_sailing_schedule.inttra_environment')

    inttra_client_id = fields.Char('INTTRA Client ID', config_parameter='fm_inttra_sailing_schedule.inttra_client_id')
    inttra_client_secret = fields.Char('INTTRA Client Secret', config_parameter='fm_inttra_sailing_schedule.inttra_client_secret')
    inttra_grant_type = fields.Char('INTTRA Grant Type', default='client_credentials', config_parameter='fm_inttra_sailing_schedule.inttra_grant_type')
