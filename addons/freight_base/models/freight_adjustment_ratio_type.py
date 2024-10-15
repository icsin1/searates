from odoo import models, fields, api


class AdjustmentRationType(models.Model):
    _name = "freight.adjustment.ratio.type"
    _description = "Adjustment Ration Type"

    name = fields.Char(required=True)
    is_package_group = fields.Boolean()
