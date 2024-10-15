# -*- coding: utf-8 -*-
from odoo import models, fields


class ShipmentChangeReason(models.Model):
    _name = 'shipment.change.reason'
    _description = 'Shipment Change Reason'

    name = fields.Char(string='Reason')
    active = fields.Boolean(default=True)
