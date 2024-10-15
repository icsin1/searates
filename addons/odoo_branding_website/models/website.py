from odoo import models, fields


class websites(models.Model):
    _inherit = 'website'

    favicon = fields.Binary(default=False)
