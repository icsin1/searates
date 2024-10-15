# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class Opportunity(models.Model):
    _inherit = "crm.prospect.opportunity"

    @api.depends('customer_type')
    def _compute_road_customer_type(self):
        for rec in self:
            rec.road_customer_type = 'sending_forwarder' if rec.customer_type == "consignor" else "receiving_forwarder"

    def _inverse_road_customer_type(self):
        for rec in self:
            rec.customer_type = "agent" if rec.customer_type == 'agent' else "consignor" if rec.road_customer_type == "sending_forwarder" else "consignee"

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

    road_customer_type = fields.Selection([
        ('sending_forwarder', 'Sending Forwarder'),
        ('receiving_forwarder', 'Receiving Forwarder')
    ], default='sending_forwarder', compute="_compute_road_customer_type", inverse="_inverse_road_customer_type", store=True, readonly=False, string="Customer Type ")

    pickup_location_type_id = fields.Many2one('freight.location.type', string="Pickup Location Type")
    delivery_location_type_id = fields.Many2one('freight.location.type', string="Delivery Location Type")
    road_origin_un_location_id = fields.Many2one(
        "freight.un.location", string="Pickup Location", compute="_compute_road_origin_un_location_id", inverse="_inverse_road_origin_un_location_id", store=True, readonly=False)
    road_destination_un_location_id = fields.Many2one(
        "freight.un.location", string="Delivery Location", compute="_compute_road_destination_un_location_id", inverse="_inverse_road_destination_un_location_id", store=True, readonly=False)
    pickup_zipcode = fields.Char()
    delivery_zipcode = fields.Char()

    @api.onchange('transport_mode_id')
    def _onchange_transport_mode_id(self):
        super()._onchange_transport_mode_id()
        values = {}
        if self.lead_id and self.lead_id.pickup_location_id.id != self.road_origin_un_location_id.id or not self.lead_id:
            values.update({
                'road_origin_un_location_id': False
            })
        else:
            values.update({
                'road_origin_un_location_id': self.lead_id.pickup_location_id.id,
            })
        if self.lead_id and self.lead_id.delivery_location_id.id != self.road_destination_un_location_id.id or not self.lead_id:
            values.update({
                'road_destination_un_location_id': False
            })
        else:
            values.update({
                'road_destination_un_location_id': self.lead_id.delivery_location_id.id,
            })
        if self.lead_id and self.lead_id.pickup_location_type_id != self.pickup_location_type_id or not self.lead_id:
            values.update({
                'pickup_location_type_id': False
            })
        else:
            values.update({
                'pickup_location_type_id': self.lead_id.pickup_location_type_id.id,
            })
        if self.lead_id and self.lead_id.delivery_location_type_id != self.delivery_location_type_id or not self.lead_id:
            values.update({
                'delivery_location_type_id': False
            })
        else:
            values.update({
                'delivery_location_type_id': self.lead_id.delivery_location_type_id.id,
            })
        self.update(values)

    @api.onchange('origin_country_id', 'pickup_location_type_id')
    def _onchange_road_pickup_location(self):
        lead = self.lead_id
        if lead and lead.pickup_country_id.id == self.origin_country_id.id and lead.pickup_location_type_id == self.pickup_location_type_id:
            location = lead.pickup_location_id.id
        else:
            location = False
        self.update({
            'road_origin_un_location_id': location,
            'origin_un_location_id': location,
        })

    @api.onchange('destination_country_id', 'delivery_location_type_id')
    def _onchange_road_delivery_location(self):
        lead = self.lead_id
        if lead and lead.delivery_country_id.id == self.destination_country_id.id and lead.delivery_location_type_id == self.delivery_location_type_id:
            location = lead.delivery_location_id.id
        else:
            location = False
        self.update({
            'road_destination_un_location_id': location,
            'destination_un_location_id': location,
        })

    # @api.constrains('road_origin_un_location_id', 'road_destination_un_location_id')
    # def _check_road_pickup_destination(self):
    #     for opportunity in self.filtered(lambda l: l.road_origin_un_location_id and l.road_destination_un_location_id):
    #         if opportunity.road_origin_un_location_id.id == opportunity.road_destination_un_location_id.id:
    #             raise ValidationError(_("Pickup and Destination location can't be same."))
