# -*- coding: utf-8 -*-

from odoo import fields, models


class FreightHouseShipment(models.Model):
    _inherit = 'freight.house.shipment'

    ams_no = fields.Integer('AMS Number')
    it_number = fields.Integer('IT Number')
    aes_number = fields.Integer('AES Number')
