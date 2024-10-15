# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProspectLead(models.Model):
    _inherit = "crm.prospect.lead"

    pickup_country_id = fields.Many2one("res.country", string="Pickup Country")
    pickup_location_type_id = fields.Many2one('freight.location.type', string="Pickup Location Type")
    pickup_location_id = fields.Many2one(
        'freight.un.location', string="Pickup Location", domain="[('has_road', '=', True), ('country_id', '=', pickup_country_id), ('location_type_id', '=', pickup_location_type_id)]")
    delivery_country_id = fields.Many2one("res.country", string="Delivery Country")
    delivery_location_type_id = fields.Many2one('freight.location.type', string="Delivery Location Type")
    delivery_location_id = fields.Many2one(
        'freight.un.location', string="Delivery Location", domain="[('has_road', '=', True), ('country_id', '=', delivery_country_id), ('location_type_id', '=', delivery_location_type_id)]")

    @api.onchange('origin_country_id')
    def _onchange_origin_country_id(self):
        if self.port_of_loading_id.country_id.id != self.origin_country_id.id:
            self.port_of_loading_id = False

    @api.onchange('destination_country_id')
    def _onchange_destination_country_id(self):
        if self.port_of_discharge_id.country_id.id != self.destination_country_id.id:
            self.port_of_discharge_id = False


    @api.onchange('transport_mode_id')
    def _onchange_transport_mode_id(self):
        super()._onchange_transport_mode_id()
        self.update({
            'pickup_country_id': False,
            'pickup_location_type_id': False,
            'pickup_location_id': False,
            'delivery_country_id': False,
            'delivery_location_type_id': False,
            'delivery_location_id': False,
        })

    @api.onchange('pickup_country_id', 'pickup_location_type_id')
    def _onchange_road_pickup_location(self):
        if self.pickup_location_id:
            if (self.pickup_country_id and self.pickup_country_id.id != self.pickup_location_id.country_id.id) or (
                    self.pickup_location_type_id and self.pickup_location_type_id != self.pickup_location_id.location_type_id):
                self.update({
                    'pickup_location_id': False,
                })

    @api.onchange('delivery_country_id', 'delivery_location_type_id')
    def _onchange_road_delivery_location(self):
        if self.delivery_location_id:
            if (self.delivery_country_id and self.delivery_country_id.id != self.delivery_location_id.country_id.id) or (
                    self.delivery_location_type_id and self.delivery_location_type_id != self.delivery_location_id.location_type_id):
                self.update({
                    'delivery_location_id': False,
                })

    @api.constrains('pickup_location_id', 'delivery_location_id')
    def _check_road_pickup_destination(self):
        for lead in self.filtered(lambda l: l.pickup_location_id and l.delivery_location_id):
            if lead.pickup_location_id.id == lead.delivery_location_id.id:
                raise ValidationError(_("Pickup and Delivery location can't be same."))

    def action_create_opportunity(self):
        self.ensure_one()
        action = super().action_create_opportunity()
        if self.mode_type == 'land':
            action['context'].update({
                'default_origin_country_id': self.pickup_country_id.id,
                'default_pickup_location_type_id': self.pickup_location_type_id.id,
                'default_origin_un_location_id': self.pickup_location_id.id,
                'default_destination_country_id': self.delivery_country_id.id,
                'default_delivery_location_type_id': self.delivery_location_type_id.id,
                'default_destination_un_location_id': self.delivery_location_id.id,
            })
        return action
