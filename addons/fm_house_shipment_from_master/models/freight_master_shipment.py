# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import ValidationError


class FreightMasterShipment(models.Model):
    _inherit = 'freight.master.shipment'

    def fetch_transportation_details_from_master(self, house_shipment_id):
        self.ensure_one()
        transportation_detail_ids = self.transportation_detail_ids.filtered(lambda t: not t.house_shipment_id)
        if transportation_detail_ids:
            transportation_detail_ids.write({
                'house_shipment_id': house_shipment_id.id,
            })

    def _prepare_master_shipment_route_vals(self):
        route_ids = []
        for route in self.route_ids:
            route_data = {
                'name': route.name,
                'route_type': route.route_type,
                'transport_mode_id': route.transport_mode_id.id,
                'transport_mode_type': route.transport_mode_type,
                'from_location_id': route.from_location_id.id,
                'to_location_id': route.to_location_id.id,
                'carrier_id': route.carrier_id.id,
                'vessel_id': route.vessel_id.id,
                'obl_number': route.obl_number,
                'voyage_number': route.voyage_number,
                'etd_time': route.etd_time,
                'eta_time': route.eta_time,
                'atd_time': route.atd_time,
                'ata_time': route.ata_time,
                'empty_container': route.empty_container,
                'empty_container_reference': route.empty_container_reference,
                'carrier_transport_mode': route.carrier_transport_mode,
                'carrier_driver_name': route.carrier_driver_name,
                'carrier_vehicle_number': route.carrier_vehicle_number,
                'remarks': route.remarks,
                'flight_number': route.flight_number,
                'mawb_number': route.mawb_number
            }
            route_ids.append(route_data)
        return route_ids

    def _prepare_house_shipment_values(self):
        self.ensure_one()
        route_ids = []
        if self.route_ids:
            route_ids = [(0, 0, val) for val in self._prepare_master_shipment_route_vals()]
        shipment_vals = {
            'state': 'created',
            'parent_id': self.id,
            'packaging_mode': self.packaging_mode,
            'company_id': self.company_id.id,
            'shipment_date': self.shipment_date,
            'transport_mode_id': self.transport_mode_id.id,
            'cargo_type_id': self.cargo_type_id.id,
            'shipment_type_id': self.shipment_type_id.id,
            'service_mode_id': self.service_mode_id.id,
            'pack_unit': self.pack_unit,
            'pack_unit_uom_id': self.pack_unit_uom_id.id,
            'gross_weight_unit': self.gross_weight_unit,
            'gross_weight_unit_uom_id': self.gross_weight_unit_uom_id.id,
            'volume_unit': self.volume_unit,
            'volume_unit_uom_id': self.volume_unit_uom_id.id,
            'net_weight_unit': self.net_weight_unit,
            'net_weight_unit_uom_id': self.net_weight_unit_uom_id.id,
            'weight_volume_unit': self.weight_volume_unit,
            'weight_volume_unit_uom_id': self.weight_volume_unit_uom_id.id,
            'origin_port_un_location_id': self.origin_port_un_location_id.id,
            'destination_port_un_location_id': self.destination_port_un_location_id.id,
            'origin_un_location_id': self.origin_un_location_id.id,
            'destination_un_location_id': self.destination_un_location_id.id,
            'sales_agent_id': self.sales_agent_id.id,
            'is_courier_shipment': self.is_courier_shipment,
            'route_ids': route_ids,
            'pickup_country_id': self.pickup_country_id.id,
            'delivery_country_id': self.delivery_country_id.id,
            'pickup_location_type_id': self.pickup_location_type_id.id,
            'delivery_location_type_id': self.delivery_location_type_id.id,
            'pickup_zipcode': self.pickup_zipcode,
            'delivery_zipcode': self.delivery_zipcode,
            'atd_time': self.atd_time,
            'ata_time': self.ata_time
        }
        if self.mode_type in ['air', 'sea']:
            shipment_vals.update({
                'etd_time': self.etd_time,
                'eta_time': self.eta_time,
            })

        if self.mode_type == 'land':
            shipment_vals.update({
                'etp_time': self.etp_time,
                'etd_time': self.etd_time,
                'origin_un_location_id': self.road_origin_un_location_id.id,
                'destination_un_location_id': self.road_destination_un_location_id.id,
            })

        shipment_partners = []
        for partner in self.shipment_partner_ids:
            if partner.partner_type_id:
                if partner.partner_type_id == self.env.ref('freight_base.org_type_customer'):
                    shipment_vals.update({
                        'client_id': partner.partner_id.id,
                        'client_address_id': partner.party_address_id.id,
                    })
                elif partner.partner_type_id == self.env.ref('freight_base.org_type_destination_agent'):
                    shipment_vals.update({
                        'client_id': partner.partner_id.id,
                        'client_address_id': partner.party_address_id.id,
                    })
                shipment_partners.append((0, 0, {
                    'partner_id': partner.partner_id.id,
                    'party_address_id': partner.party_address_id.id,
                    'partner_type_id': partner.partner_type_id.id,  # Ensure partner type id is set
                }))
        # Update default values with shipment partners
        if shipment_partners:
            shipment_vals.update({'shipment_partner_ids': shipment_partners})

        if self.mode_type == 'air':
            shipment_vals.update({
                'voyage_number': self.voyage_number,
                'aircraft_type': 'cao' if self.aircraft_type == 'coa' else self.aircraft_type,
                'shipping_line_id': self.shipping_line_id.id})
        if 'client_id' not in shipment_vals:
            raise ValidationError(_("Client is mandatory in House Shipment.Please add it in Master Shipment"))

        return shipment_vals

    def action_create_direct_shipment(self):
        if not self.service_mode_id:
            raise ValidationError(_("Service Mode is mandatory in House Shipment.Please add it in Master Shipment"))
        shipment_vals = self._prepare_house_shipment_values()
        house_shipment_id = self.env['freight.house.shipment'].create(shipment_vals)
        self.fetch_transportation_details_from_master(house_shipment_id)
        return {
            'name': 'House Shipment',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'freight.house.shipment',
            'res_id': house_shipment_id.id
        }
