# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo import api, models, fields, _
from odoo.addons.fm_quote.models.shipment_quote import READONLY_STAGE


class ShipmentQuote(models.Model):
    _inherit = 'shipment.quote'

    transportation_pack_detail_ids = fields.One2many('quote.transportation.package.details', 'quotation_id', string="Transportation Detail", states=READONLY_STAGE, readonly=True, copy=False)
    divide_value = fields.Float(string='Divided Value', compute='_compute_volumetric_weight_calculation', store=True)

    @api.depends('transportation_pack_detail_ids',
                 'transport_mode_id',
                 'add_transportation_details',
                 'transportation_pack_detail_ids.weight')
    def _compute_volumetric_weight_calculation(self):
        volumetric_divided_value_ids = self.env['volumetric.divided.value']
        for quote in self:
            if quote.opportunity_id and quote.transportation_pack_detail_ids:
                for transportation in quote.transportation_pack_detail_ids:
                    if transportation.transport_mode_id and transportation.lwh_uom_id and transportation.mode_type == 'land':
                        volumetric_divided_value = volumetric_divided_value_ids.search([
                            ('transport_mode_id', '=', transportation.transport_mode_id.id),
                            ('uom_id', '=', transportation.lwh_uom_id.id)])
                        transportation.divided_value = volumetric_divided_value.divided_value
                        if transportation.divided_value:
                            if transportation.lwh_uom_id:
                                transportation.volumetric_weight = (transportation.length * transportation.width * transportation.height * transportation.count) / transportation.divided_value
                            else:
                                transportation.volumetric_weight = 0.0
                        else:
                            transportation.volumetric_weight = transportation.volumetric_weight

    def _prepare_transportation_detail_vals(self):
        vals = []
        for line in self.transportation_pack_detail_ids:
            vals.append({
                'truck_number_id': line.truck_number_id.id,
                'trailer_number_id': line.trailer_number_id.id,
                'container_type_id': line.container_type_id.id,
                'is_refrigerated': line.is_refrigerated,
                'container_temperature': line.container_temperature,
                'container_temperature_uom_id': line.container_temperature_uom_id.id,
                'max_temperature': line.max_temperature,
                'max_temperature_uom_id': line.max_temperature_uom_id.id,
                'stuffing_location_type_id': line.pickup_location_type_id.id,
                'stuffing_un_location_id': line.road_origin_un_location_id.id,
                'destuffing_location_type_id': line.delivery_location_type_id.id,
                'destuffing_un_location_id': line.road_destination_un_location_id.id,
                'stuffing_datetime': line.estimated_pickup,
                'destuffing_datetime': line.expected_delivery
            })
        return vals

    def _prepare_container_detail_vals(self):
        vals = []
        for line in self.transportation_pack_detail_ids:
            vals.append({
                'package_mode': 'container',
                'mode_type': line.transport_mode_id.mode_type,
                'truck_number_id': line.truck_number_id.id,
                'trailer_number_id': line.trailer_number_id.id,
                'container_type_id': line.container_type_id.id,
                'quantity': line.count,
                'pack_count': self.pack_unit,
                'is_refrigerated': line.is_refrigerated,
                'container_temperature': line.container_temperature,
                'container_temperature_uom_id': line.container_temperature_uom_id.id,
                'max_temperature': line.max_temperature,
                'max_temperature_uom_id': line.max_temperature_uom_id.id,
            })
        return vals

    def _prepare_package_detail_vals(self):
        vals = []
        for line in self.transportation_pack_detail_ids:
            vals.append({
                'package_mode': 'package',
                'truck_number_id': line.truck_number_id.id,
                'trailer_number_id': line.trailer_number_id.id,
                'package_type_id': line.pack_type_id.id,
                'quote_transport_line_id': line.id,
                'quantity': line.count,
                'is_hazardous': line.is_hazardous,
                'hbl_description': line.notes,
                'container_type_id': line.container_type_id.id,
                'commodity_ids': [(0, 0, {
                    'commodity_id': line.commodity_id.id,
                    'pieces': line.count,
                    'gross_weight': line.weight,
                    'weight_uom_id': line.weight_uom_id.id,
                    'volume': line.volume,
                    'volume_uom_id': line.volume_uom_id.id,
                    'volumetric_weight': line.volumetric_weight,
                    'volumetric_weight_uom_id': line.volumetric_weight_uom_id.id,
                    'length': line.length,
                    'width': line.width,
                    'height': line.height,
                    'divided_value': line.divided_value,
                    'dimension_uom_id': line.lwh_uom_id and line.lwh_uom_id.id or self.env.company.dimension_uom_id.id,
                    })] if line.commodity_id else [],
            })
        return vals

    def _prepare_house_shipment_values(self):
        self.ensure_one()
        values = super()._prepare_house_shipment_values()
        if self.mode_type == 'land' and self.add_transportation_details:
            transportation_detail_ids = [(0, 0, val) for val in self._prepare_transportation_detail_vals()]
            values.update({
                'default_transportation_detail_ids': transportation_detail_ids,
                'default_pickup_location_type_id': self.pickup_location_type_id.id,
                'default_delivery_location_type_id': self.delivery_location_type_id.id,
            })
            if self.is_package_group:
                package_ids = [(0, 0, val) for val in self._prepare_package_detail_vals()]
                values.update({
                    'default_package_ids': package_ids,
                })
            else:
                container_ids = [(0, 0, val) for val in self._prepare_container_detail_vals()]
                values.update({
                    'default_container_ids': container_ids,
                })
        return values

    def ensure_quote_approval(self, action='send'):
        self.ensure_one()
        if self.mode_type == 'land':
            if not self.quotation_line_ids:
                raise ValidationError(_('Add at least one charge to %s quotation.') % (action))

            total_cargo_lines = any(line.count <= 0 for line in self.quote_cargo_line_ids)
            if total_cargo_lines:
                raise ValidationError(_('Pack count must be greater than zero to %s quotation.') % (action))
        else:
           return super().ensure_quote_approval()

    @api.depends(
        'auto_update_weight_volume', 'cargo_is_package_group',
        'transportation_pack_detail_ids',
        'transportation_pack_detail_ids', 'transportation_pack_detail_ids.weight', 'transportation_pack_detail_ids.weight_uom_id', 'transportation_pack_detail_ids.volume', 'transportation_pack_detail_ids.volume_uom_id',
        'transportation_pack_detail_ids.volumetric_weight')
    def _compute_auto_update_weight_volume(self):
        volume_uom = self.env.company.volume_uom_id
        weight_uom = self.env.company.weight_uom_id
        package_uom = self.env.ref('freight_base.pack_uom_pkg')

        for quote in self:
            if quote.mode_type == 'land':
                # Keep Manual value when No auto update
                if not quote.auto_update_weight_volume or not quote.cargo_is_package_group:
                    return super()._compute_auto_update_weight_volume()
                else:
                    total_gross_weight = sum([p.weight_uom_id._compute_quantity(p.weight, weight_uom) for p in quote.transportation_pack_detail_ids])
                    total_volumetric_weight_unit = sum(quote.transportation_pack_detail_ids.mapped('volumetric_weight'))
                    total_volume_unit = sum(quote.transportation_pack_detail_ids.mapped('volume'))
                    pack_unit = sum(quote.transportation_pack_detail_ids.mapped('count'))
                    package_uom = quote.transportation_pack_detail_ids.mapped('pack_type_id') if len(quote.transportation_pack_detail_ids.mapped('pack_type_id')) == 1 else package_uom

                    quote.gross_weight_unit, quote.gross_weight_unit_uom_id = round(total_gross_weight, 3), weight_uom.id
                    quote.weight_volume_unit, quote.weight_volume_unit_uom_id = round(total_volumetric_weight_unit, 3), weight_uom.id
                    quote.volume_unit, quote.volume_unit_uom_id = round(total_volume_unit, 3), volume_uom.id
                    quote.pack_unit, quote.pack_unit_uom_id = round(pack_unit, 3), package_uom.id
            else:
                return super()._compute_auto_update_weight_volume()
