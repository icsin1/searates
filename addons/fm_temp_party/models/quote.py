# -*- coding: utf-8 -*-
from odoo import models, fields
READONLY_STAGE = {'draft': [('readonly', False)]}


class ShipmentQuote(models.Model):
    _inherit = "shipment.quote"

    enable_temp_party = fields.Boolean('Enable Temporary Party', related='company_id.enable_temp_party', help='Enable to enter Temporary Name and Address', store=True)
    temp_shipper_name = fields.Char('Shipper', states=READONLY_STAGE, readonly=True)
    temp_shipper_address = fields.Text('Shipper Address', states=READONLY_STAGE, readonly=True)
    temp_consignee_name = fields.Char('Consignee', states=READONLY_STAGE, readonly=True)
    temp_consignee_address = fields.Text('Consignee Address', states=READONLY_STAGE, readonly=True)

    def _prepare_house_shipment_values(self):
        self.ensure_one()
        default_shipment_vals = super()._prepare_house_shipment_values()
        if self.enable_temp_party:
            default_shipment_vals.update({
                'default_temp_shipper_name': self.temp_shipper_name,
                'default_temp_shipper_address': self.temp_shipper_address,
                'default_temp_consignee_name': self.temp_consignee_name,
                'default_temp_consignee_address': self.temp_consignee_address,
            })
        return default_shipment_vals

    def _prepare_service_job_vals(self):
        self.ensure_one()
        default_service_job_vals = super()._prepare_service_job_vals()
        if self.enable_temp_party:
            default_service_job_vals.update({
                'default_temp_shipper_name': self.temp_shipper_name,
                'default_temp_shipper_address': self.temp_shipper_address,
                'default_temp_consignee_name': self.temp_consignee_name,
                'default_temp_consignee_address': self.temp_consignee_address,
            })
        return default_service_job_vals
