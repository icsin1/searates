# -*- coding: utf-8 -*-

from odoo import models, fields


class FreightShipmentDocument(models.Model):
    _inherit = 'freight.house.shipment.document'

    is_publish = fields.Boolean('Publish')
