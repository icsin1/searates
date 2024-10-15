# -*- coding: utf-8 -*-

import json
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class FreightHouseShipment(models.Model):
    _inherit = 'freight.house.shipment'

    @api.depends('transport_mode_id', 'destination_port_un_location_id', 'origin_port_un_location_id',
                 'shipper_id', 'consignee_id', 'service_mode_id', 'cargo_type_id',
                 'shipment_type_id', 'transport_mode_id', 'state')
    def _compute_shipment_quote_domain(self):
        for rec in self:
            domain = [('transport_mode_id', '=', rec.transport_mode_id.id),
                      ('shipment_type_id', '=', rec.shipment_type_id.id),
                      ('cargo_type_id', '=', rec.cargo_type_id.id),
                      ('service_mode_id', '=', rec.service_mode_id.id),
                      ('port_of_loading_id', '=', rec.origin_port_un_location_id.id),
                      ('port_of_discharge_id', '=', rec.destination_port_un_location_id.id),
                      ('shipment_count', '=', 'multiple'), ('state', '=', 'accept'), ('quote_for', '=', 'shipment'),
                      '|', ('shipper_id', '=', rec.shipper_id.id), ('shipper_id', '=', False),
                      '|', ('consignee_id', '=', rec.consignee_id.id), ('consignee_id', '=', False),
                      ]
            rec.shipment_quote_domain = json.dumps(domain)

    shipment_quote_domain = fields.Char(compute='_compute_shipment_quote_domain', store=True)
    shipment_quote_id = fields.Many2one('shipment.quote', string='Shipment Quote', copy=False)

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        record = super(FreightHouseShipment, self).copy(default)
        record.shipment_quote_id = False
        return record

    @api.model_create_single
    def create(self, values):
        rec = super().create(values)
        # Fetch Packages from quote
        if rec.shipment_quote_id and rec.cargo_is_package_group:
            rec.package_ids = [(5, 0, 0)]
            rec.action_fetch_from_quote()
        return rec

    def action_shipment_quote(self):
        self.ensure_one()
        return {
            'name': 'Quotes',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'shipment.quote',
            'domain': [('id', '=', self.shipment_quote_id.id)],
            'res_id': self.shipment_quote_id.id,
        }

    def action_fetch_from_quote(self):
        self.ensure_one()
        quote = self.shipment_quote_id
        if self.cargo_is_package_group and self.package_ids:
            raise ValidationError(_('Remove existing packages to Fetch package data from Quote.'))
        if not self.cargo_is_package_group and self.container_ids:
            raise ValidationError(_('Remove existing container to Fetch container data from Quote.'))
        if self.cargo_is_package_group:
            # Package - LCL
            self.package_ids = [(0, 0, vals) for vals in quote._prepare_quote_container_package_vals()]
        else:
            # Container - FCL
            self.container_ids = [(0, 0, vals) for vals in quote._prepare_quote_container_package_vals()]
        self.with_context(force_change=True)._compute_auto_weight_volume()

    @api.onchange('transport_mode_id')
    def _onchange_transport_mode_id(self):
        values = {}
        # Quote to House Shipment
        if self._name == 'freight.house.shipment' and self.shipment_quote_id:
            if self.shipment_quote_id.transport_mode_id.id != self.transport_mode_id.id or not self.shipment_quote_id:
                values.update({
                    'cargo_type_id': False,
                    'origin_port_un_location_id': False,
                    'destination_port_un_location_id': False,
                })
            else:
                values.update({
                    'cargo_type_id': self.shipment_quote_id.cargo_type_id.id,
                    'origin_port_un_location_id': self.shipment_quote_id.port_of_loading_id.id,
                    'destination_port_un_location_id': self.shipment_quote_id.port_of_discharge_id.id,
                })
            self.update(values)
        else:
            super()._onchange_transport_mode_id()

    @api.constrains('shipment_quote_id', 'cargo_type_id', 'transport_mode_id', 'shipment_type_id', 'service_mode_id',
                    'shipper_id', 'consignee_id', 'client_id', 'origin_un_location_id', 'destination_un_location_id',
                    'origin_port_un_location_id', 'destination_port_un_location_id')
    def _check_shipment_quote_values(self):
        for shipment in self.filtered(lambda s: s.shipment_quote_id):
            shipment_quote = shipment.shipment_quote_id
            unmatched_field_list = []
            if (shipment_quote.cargo_type_id and shipment.cargo_type_id
                    and shipment_quote.cargo_type_id.id != shipment.cargo_type_id.id):
                unmatched_field_list.append(self._fields['cargo_type_id'].string)
            if (shipment_quote.transport_mode_id and shipment.transport_mode_id
                    and shipment_quote.transport_mode_id.id != shipment.transport_mode_id.id):
                unmatched_field_list.append(self._fields['transport_mode_id'].string)
            if (shipment_quote.shipment_type_id and shipment.shipment_type_id
                    and shipment_quote.shipment_type_id.id != shipment.shipment_type_id.id):
                unmatched_field_list.append(self._fields['shipment_type_id'].string)
            if (shipment_quote.service_mode_id and shipment.service_mode_id
                    and shipment_quote.service_mode_id.id != shipment.service_mode_id.id):
                unmatched_field_list.append(self._fields['service_mode_id'].string)
            if (shipment_quote.client_id and shipment.client_id
                    and shipment_quote.client_id.id != shipment.client_id.id):
                unmatched_field_list.append(self._fields['client_id'].string)
            if (shipment_quote.shipper_id and shipment.shipper_id
                    and shipment_quote.shipper_id.id != shipment.shipper_id.id and not shipment.company_id.shipment_allow_shipper_consignee_change):
                unmatched_field_list.append(self._fields['shipper_id'].string)
            if (shipment_quote.consignee_id and shipment.consignee_id
                    and shipment_quote.consignee_id.id != shipment.consignee_id.id and not shipment.company_id.shipment_allow_shipper_consignee_change):
                unmatched_field_list.append(self._fields['consignee_id'].string)
            if (shipment_quote.origin_un_location_id and shipment.origin_un_location_id
                    and shipment_quote.origin_un_location_id.id != shipment.origin_un_location_id.id):
                unmatched_field_list.append(self._fields['origin_un_location_id'].string)
            if (shipment_quote.destination_un_location_id and shipment.destination_un_location_id
                    and shipment_quote.destination_un_location_id.id != shipment.destination_un_location_id.id):
                unmatched_field_list.append(self._fields['destination_un_location_id'].string)
            if (shipment_quote.port_of_loading_id and shipment.origin_port_un_location_id
                    and shipment_quote.port_of_loading_id.id != shipment.origin_port_un_location_id.id):
                unmatched_field_list.append(self._fields['origin_port_un_location_id'].string)
            if (shipment_quote.port_of_discharge_id and shipment.destination_port_un_location_id
                    and shipment_quote.port_of_discharge_id.id != shipment.destination_port_un_location_id.id):
                unmatched_field_list.append(self._fields['destination_port_un_location_id'].string)
            if unmatched_field_list:
                string_mess_list = []
                for each in unmatched_field_list:
                    string_mess_list.append(each + " must match with " + each + " from Quote.")
                raise ValidationError(_("Below list of field(s) must match with Quote : %s \n%s") % (shipment_quote.name, '\n'.join(string_mess_list)))

    @api.onchange('is_courier_shipment')
    def _onchange_is_courier_shipment(self):
        if not self.shipment_quote_id:
            return super()._onchange_is_courier_shipment()
        else:
            if not self._origin and self.shipment_quote_id:
                if not self.shipment_quote_id.is_courier_shipment:
                    self.is_courier_shipment = False
                else:
                    self.is_courier_shipment = True
