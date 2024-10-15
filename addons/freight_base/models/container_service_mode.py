from odoo import models


class ContainerServiceMode(models.Model):
    _name = 'container.service.mode'
    _inherit = 'freight.service.mode'
    _description = 'Container Service Mode'
