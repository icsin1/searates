# -*- coding: utf-8 -*-

from odoo import models, fields


class FreightTransportMixin(models.Model):
    _name = "freight.transport.mixin"
    _description = "Transportation Details Mixin"

    truck_number_id = fields.Many2one('freight.truck.number', string="Truck Number", required=1)
    trailer_number_id = fields.Many2one('freight.truck.trailer.number', string="Trailer Number")
    service_name = fields.Char()
    pickup_location_type_id = fields.Many2one('freight.location.type', string="Pickup Location Type")
    road_origin_un_location_id = fields.Many2one("freight.un.location", string="Pickup Location",
                                                 domain="[('location_type_id', '=', pickup_location_type_id)]")
    delivery_location_type_id = fields.Many2one('freight.location.type', string="Delivery Location Type")
    road_destination_un_location_id = fields.Many2one("freight.un.location", string="Delivery Location",
                                                      domain="[('location_type_id', '=', delivery_location_type_id)]")
