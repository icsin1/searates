# -*- coding: utf-8 -*-

from odoo import models, fields


class Opportunity(models.Model):
    _inherit = "crm.prospect.opportunity"

    add_transportation_details = fields.Boolean()
    transportation_detail_ids = fields.One2many('opportunity.transportation.details', 'opportunity_id', string="Transportation Detail")

    def action_create_quotation(self):
        self.ensure_one()
        action = super().action_create_quotation()
        if self.mode_type == 'land' and self.add_transportation_details:
            action['context'].update({
                'default_add_transportation_details': self.add_transportation_details,
                'default_transportation_pack_detail_ids': self._prepare_transport_pack_details_vals(),
            })
        return action

    def _prepare_transport_pack_details_vals(self):
        vals = []
        for detail in self.transportation_detail_ids:
            vals.append((0, 0, {
                'container_type_id': detail.container_type_id.id,
                'pack_type_id': detail.package_uom_id.id,
                'weight_uom_id': detail.weight_uom_id.id,
                'volume_uom_id': detail.volume_uom_id.id,
                'weight': detail.weight,
                'volume': detail.volume,
                'count': detail.quantity,
                'length': detail.length,
                'width': detail.width,
                'height': detail.height,
                'lwh_uom_id': detail.lwh_uom_id and detail.lwh_uom_id.id or self.env.company.dimension_uom_id.id,
                'divided_value': detail.divided_value,
                'estimated_pickup': detail.estimated_pickup,
                'expected_delivery': detail.expected_delivery,
                'transit_time': detail.transit_time,
                'truck_number_id': detail.truck_number_id.id,
                'trailer_number_id': detail.trailer_number_id.id,
                'service_name': detail.service_name,
                'pickup_location_type_id': detail.pickup_location_type_id.id,
                'road_origin_un_location_id': detail.road_origin_un_location_id.id,
                'delivery_location_type_id': detail.delivery_location_type_id.id,
                'road_destination_un_location_id': detail.road_destination_un_location_id.id,
                'is_refrigerated': detail.is_refrigerated,
                'container_temperature': detail.container_temperature,
                'container_temperature_uom_id': detail.container_temperature_uom_id.id,
                'max_temperature_uom_id': detail.max_temperature_uom_id.id,
                'max_temperature': detail.max_temperature,
            }))
        return vals
