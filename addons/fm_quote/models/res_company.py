# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    enable_quote_routing = fields.Boolean(string="Enable Quote Routing", readonly=False)
    shipment_allow_shipper_consignee_change = fields.Boolean(string="Shipper/Consignee Updation", readonly=False)

    def _create_per_company_freight_sequence(self):
        super()._create_per_company_freight_sequence()
        company_sequence = self.env.ref('fm_quote.sequence_freight_quotation')
        if company_sequence.company_id != self:
            company_sequence = company_sequence.copy({'company_id': self.id})
        self.env['freight.sequence'].create({
            'name': 'Shipment Quote',
            'ir_model_id': self.env.ref('fm_quote.model_shipment_quote').id,
            'ir_field_id': self.env.ref('fm_quote.field_shipment_quote__name').id,
            'ir_sequence_id': company_sequence.id,
            'sequence_format': 'QT-{{object.transport_mode_id.code}}-{{ object.shipment_type_id.code}}-{{ object.cargo_type_id.code }}',
            'number_increment': 1,
            'padding': 5,
            'company_id': self.id
        })
