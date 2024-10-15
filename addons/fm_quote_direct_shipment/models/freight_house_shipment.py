# -*- coding: utf-8 -*-
from odoo import models, fields, api


class FreightHouseShipment(models.Model):
    _inherit = 'freight.house.shipment'

    create_shipment_for = fields.Selection(related='company_id.create_shipment_for', store=True)
    is_quote_direct_shipment = fields.Boolean(copy=False)

    @api.constrains('hbl_number', 'state')
    def _check_unique_hbl_number(self):
        self = self.filtered(lambda shipment: not shipment.is_quote_direct_shipment)
        return super(FreightHouseShipment, self)._check_unique_hbl_number()

    @api.depends('is_quote_direct_shipment')
    def _compute_external_carrier_bookings(self):
        super()._compute_external_carrier_bookings()
        for shipment in self:
            if shipment.is_quote_direct_shipment:
                shipment.allow_edit_external_carrier_bookings = True
