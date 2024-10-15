# -*- coding: utf-8 -*-
from odoo import models


class ShipmentQuote(models.Model):
    _inherit = 'shipment.quote'

    def prepare_tariff_service_wizard_vals(self):
        self.ensure_one()
        tariff_service_vals = super().prepare_tariff_service_wizard_vals()
        if self.quote_for == 'job':
            tariff_service_vals.update({'service_job_type_id': self.service_job_type_id.id, 'ignore_location': True})
        return tariff_service_vals
