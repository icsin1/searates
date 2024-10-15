# -*- coding: utf-8 -*-

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    enable_disable_part_bl = fields.Boolean(string="Enable Part BL", readonly=False)
    enable_disable_reexport_hs = fields.Boolean(string="Enable ReExport Shipment", readonly=False)
    enable_cut_off_dates = fields.Boolean()
    enable_feeder_details = fields.Boolean()
    enable_disable_shipping_line = fields.Boolean(string="Enable SCAC Code", readonly=False)
    allow_edit_external_carrier_bookings = fields.Boolean('Allow edit of External Carrier Bookings', readonly=False)
    shipment_status_change = fields.Boolean(string="Shipment Status Change", readonly=False)

    def _create_per_company_freight_sequence(self):
        super()._create_per_company_freight_sequence()
        freight_sequence_obj = self.env['freight.sequence']
        val_lst = []
        company_sequence = self.env.ref('freight_management.sequence_master_freight_shipment')
        if company_sequence.company_id != self:
            company_sequence = company_sequence.copy({'company_id': self.id})
        master_shipment_vals = {
            'name': 'Master Shipment',
            'ir_model_id': self.env.ref('freight_management.model_freight_master_shipment').id,
            'ir_field_id': self.env.ref('freight_management.field_freight_master_shipment__name').id,
            'ir_sequence_id': company_sequence.id,
            'sequence_format': '{{object.transport_mode_id.code}}-{{ object.shipment_type_id.code[0] }}-{{object.cargo_type_id.code}}-M',
            'number_increment': 1,
            'padding': 5,
            'company_id': self.id
        }
        val_lst.append(master_shipment_vals)
        company_sequence = self.env.ref('freight_management.sequence_house_freight_shipment')
        if company_sequence.company_id != self:
            company_sequence = company_sequence.copy({'company_id': self.id})
        house_shipment_vals = {
            'name': 'House Shipment',
            'ir_model_id': self.env.ref('freight_management.model_freight_house_shipment').id,
            'ir_field_id': self.env.ref('freight_management.field_freight_house_shipment__booking_nomination_no').id,
            'ir_sequence_id': company_sequence.id,
            'sequence_format': "{{object.transport_mode_id.code}}-{{object.shipment_type_id.code[0]}}-{{object.cargo_type_id.code}}-H-{{'N' if object.hbl_number_type == 'nomination_no' else 'F'}}",
            'number_increment': 1,
            'padding': 5,
            'company_id': self.id
        }
        val_lst.append(house_shipment_vals)
        if val_lst:
            freight_sequence_obj.create(val_lst)
