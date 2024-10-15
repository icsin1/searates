from odoo import models, fields


class ContainerCategory(models.Model):
    _name = "freight.container.category"
    _description = "Container Category"

    name = fields.Char("Category Name", required=True)
    description = fields.Text()
    is_refrigerated = fields.Boolean(default=False)
    active = fields.Boolean(default=True)
    is_oog_container = fields.Boolean(default=False)
