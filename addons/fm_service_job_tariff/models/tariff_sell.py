# -*- coding: utf-8 -*-
import json
from odoo import models, api


class TariffSell(models.Model):
    _inherit = 'tariff.sell'

    @api.depends('customer_id', 'shipment_type_id', 'transport_mode_id', 'cargo_type_id', 'origin_id', 'destination_id', 'service_job_type_id')
    def _compute_tariff_name(self):
        for rec in self.filtered(lambda ts: ts.tariff_for == 'job'):
            location_suffix = ''
            if rec.origin_id:
                location_suffix = '-{}'.format(rec.origin_id.loc_code)
            if rec.destination_id:
                location_suffix = '{}-{}'.format(location_suffix, rec.destination_id.loc_code)
            tariff_name = ''
            if rec.customer_id:
                tariff_name = '{}-'.format(rec.customer_id.name or '')
            tariff_name = '{}{}{}'.format(
                tariff_name,
                rec.service_job_type_id and str(rec.service_job_type_id.name).strip()[:2] or '',
                location_suffix
            )
            rec.tariff_name = tariff_name
        super()._compute_tariff_name()


class TariffSellLine(models.Model):
    _inherit = 'tariff.sell.line'

    def get_charge_domain(self):
        self.ensure_one()
        if self.sell_tariff_id and self.sell_tariff_id.tariff_for == 'job':
            charge_category = self.env.ref('fm_service_job.job_charge_category', raise_if_not_found=False)
            return json.dumps(['|', ('company_id', '=', self.company_id.id), ('company_id', '=', False), ('categ_id', '=', charge_category.id)])
        else:
            return super().get_charge_domain()
