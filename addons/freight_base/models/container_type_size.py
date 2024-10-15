from odoo import models, fields


class ContainerTypeSize(models.Model):
    _name = "freight.container.type.size"
    _description = "Container Type Size"

    name = fields.Char("Container Size", required=True)
    container_type_ids = fields.Many2many('freight.container.type', string='Container Type')
    active = fields.Boolean(default=True)
