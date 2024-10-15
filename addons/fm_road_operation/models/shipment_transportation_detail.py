# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ShipmentTransportationDetails(models.Model):
    _name = "freight.shipment.transportation.details"
    _inherit = ['freight.transport.mixin']
    _description = "House Shipment Transportation Details"

    @api.depends('house_shipment_id.container_ids', 'house_shipment_id.package_ids', 'container_type_id')
    def _compute_allowed_container_number_ids(self):
        for record in self:
            if record.house_shipment_id.packaging_mode == "package":
                house_package_ids = record.house_shipment_id.package_ids
            else:
                house_package_ids = record.house_shipment_id.container_ids
            record.allowed_container_number_ids = house_package_ids.mapped('container_number')

    house_shipment_id = fields.Many2one('freight.house.shipment', string="House Shipment")
    master_shipment_id = fields.Many2one('freight.master.shipment', string="Master Shipment")
    truck_owned_by = fields.Selection(related="truck_number_id.truck_owned_by", store=True, readonly=False)
    truck_type_id = fields.Many2one('truck.type', related='truck_number_id.truck_type_id', store=True, readonly=False)
    driver_name = fields.Char()
    driver_mobile_number = fields.Char(string="Driver Mobile No.")
    carrier_id = fields.Many2one('freight.carrier', string='Transporter Name')
    stuffing_location_type_id = fields.Many2one('freight.location.type', string="Stuffing Location Type")
    stuffing_un_location_id = fields.Many2one("freight.un.location", string="Stuffing Location")
    stuffing_datetime = fields.Datetime()
    destuffing_location_type_id = fields.Many2one('freight.location.type', string="Destuffing Location Type")
    destuffing_un_location_id = fields.Many2one("freight.un.location", string="Destuffing Location")
    destuffing_datetime = fields.Datetime()
    container_type_id = fields.Many2one('freight.container.type', string="Truck Type")
    container_number_id = fields.Many2one('freight.master.shipment.container.number', string="Container Number")
    allowed_container_number_ids = fields.Many2many('freight.master.shipment.container.number',
                                                    compute='_compute_allowed_container_number_ids')
    transport_mode_id = fields.Many2one('transport.mode', string="Transport Mode")

    @api.constrains('stuffing_un_location_id', 'destuffing_un_location_id')
    def _check_road_pickup_destination(self):
        for record in self.filtered(lambda line: line.stuffing_un_location_id and line.destuffing_un_location_id):
            if record.stuffing_un_location_id.id == record.destuffing_un_location_id.id:
                raise ValidationError(_("Stuffing and Destuffing location can't be same."))

    @api.onchange('stuffing_location_type_id')
    def _onchange_stuffing_location_type_id(self):
        self.stuffing_un_location_id = False

    @api.onchange('destuffing_location_type_id')
    def _onchange_destuffing_location_type_id(self):
        self.destuffing_un_location_id = False

    @api.constrains('stuffing_datetime', 'destuffing_datetime')
    def _check_shipment_eta_etd_time(self):
        for record in self:
            if record.stuffing_datetime and record.destuffing_datetime and (record.stuffing_datetime > record.destuffing_datetime):
                raise ValidationError(_(
                    'Stuffing date should be less than destuffing date.'))
