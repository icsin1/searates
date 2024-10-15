# -*- coding: utf-8 -*-
from odoo import models, fields


class FreightShipmentTag(models.Model):
    _name = 'freight.shipment.tag'
    _description = 'Shipment Tags'

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Tag-Name must be unique !'),
    ]
