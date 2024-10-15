# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.addons.fm_quote.models.shipment_quote import READONLY_STAGE


class ShipmentQuote(models.Model):
    _inherit = "shipment.quote"

    @api.depends('origin_un_location_id')
    def _compute_road_origin_un_location_id(self):
        for rec in self:
            rec.road_origin_un_location_id = rec.origin_un_location_id.id

    def _inverse_road_origin_un_location_id(self):
        for rec in self:
            rec.origin_un_location_id = rec.road_origin_un_location_id.id

    @api.depends('destination_un_location_id')
    def _compute_road_destination_un_location_id(self):
        for rec in self:
            rec.road_destination_un_location_id = rec.destination_un_location_id.id

    def _inverse_road_destination_un_location_id(self):
        for rec in self:
            rec.destination_un_location_id = rec.road_destination_un_location_id.id

    pickup_location_type_id = fields.Many2one('freight.location.type', string="Pickup Location Type")
    delivery_location_type_id = fields.Many2one('freight.location.type', string="Delivery Location Type")
    road_origin_un_location_id = fields.Many2one("freight.un.location", string="Pickup Location",
                                                 compute="_compute_road_origin_un_location_id",
                                                 inverse="_inverse_road_origin_un_location_id",
                                                 store=True, readonly=False)
    road_destination_un_location_id = fields.Many2one("freight.un.location", string="Delivery Location",
                                                      compute="_compute_road_destination_un_location_id",
                                                      inverse="_inverse_road_destination_un_location_id",
                                                      store=True, readonly=False)
    pickup_zipcode = fields.Char()
    delivery_zipcode = fields.Char()
    add_transportation_details = fields.Boolean()
    transportation_detail_ids = fields.One2many('quote.transportation.details', 'shipment_quote_id', string="Transportation Detail")

    shipper_id = fields.Many2one('res.partner', string='Sending Forwarder',
                                 domain="[('type', '=', 'contact'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 states=READONLY_STAGE, readonly=True)
    consignee_id = fields.Many2one('res.partner', string='Receiving Forwarder',
                                   domain="[('type', '=', 'contact'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                   states=READONLY_STAGE, readonly=True)

    @api.onchange('origin_country_id', 'pickup_location_type_id')
    def _onchange_road_pickup_location(self):
        opportunity = self.opportunity_id
        if opportunity and opportunity.origin_country_id.id == self.origin_country_id.id and opportunity.pickup_location_type_id == self.pickup_location_type_id:
            location = opportunity.road_origin_un_location_id.id
        else:
            location = False
        self.update({
            'road_origin_un_location_id': location,
        })

    @api.onchange('destination_country_id', 'delivery_location_type_id')
    def _onchange_road_delivery_location(self):
        opportunity = self.opportunity_id
        if opportunity and opportunity.destination_country_id.id == self.destination_country_id.id and opportunity.delivery_location_type_id == self.delivery_location_type_id:
            location = opportunity.road_destination_un_location_id.id
        else:
            location = False
        self.update({
            'road_destination_un_location_id': location,
        })

    # NOTE: Road freight no need to have this validation
    # @api.constrains('road_origin_un_location_id', 'road_destination_un_location_id')
    # def _check_origin_destination_un_location(self):
    #     for rec in self.filtered(lambda quote: quote.mode_type == 'land'):
    #         if rec.road_origin_un_location_id and rec.road_destination_un_location_id and rec.road_origin_un_location_id == rec.road_destination_un_location_id:
    #             raise ValidationError(_('Origin and Destination Location Must be Different, It can not same.'))

    def _prepare_transportation_detail_vals(self):
        self.ensure_one()
        transport_details = []
        for line in self.transportation_detail_ids:
            transport_details.append({
                'truck_number_id': line.truck_number_id.id,
                'trailer_number_id': line.trailer_number_id.id,
                'stuffing_location_type_id': line.pickup_location_type_id.id,
                'stuffing_un_location_id': line.road_origin_un_location_id.id,
                'destuffing_location_type_id': line.delivery_location_type_id.id,
                'destuffing_un_location_id': line.road_destination_un_location_id.id,
                'stuffing_datetime': line.estimated_pickup,
                'destuffing_datetime': line.expected_delivery,
            })
        return transport_details

    def _prepare_house_shipment_values(self):
        default_shipment_vals = super()._prepare_house_shipment_values()
        transportation_detail_ids = [(0, 0, val) for val in self._prepare_transportation_detail_vals()]
        default_shipment_vals.update({
            'default_pickup_country_id': self.origin_country_id.id,
            'default_delivery_country_id': self.destination_country_id.id,
            'default_pickup_location_type_id': self.pickup_location_type_id.id,
            'default_delivery_location_type_id': self.delivery_location_type_id.id,
            'default_origin_un_location_id': self.road_origin_un_location_id.id,
            'default_destination_un_location_id': self.road_destination_un_location_id.id,
            'default_transportation_detail_ids': transportation_detail_ids,
            'default_pickup_zipcode': self.pickup_zipcode,
            'default_delivery_zipcode': self.delivery_zipcode,
        })
        if self.mode_type == 'land':
            default_shipment_vals.update({
                'default_etp_time': self.estimated_pickup,
                'default_etd_time': self.expected_delivery,
            })
        return default_shipment_vals
