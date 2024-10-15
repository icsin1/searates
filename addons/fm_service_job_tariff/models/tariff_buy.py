# -*- coding: utf-8 -*-
import json
from odoo import models, api


class TariffBuy(models.Model):
    _inherit = 'tariff.buy'

    @api.depends('vendor_id', 'shipment_type_id', 'transport_mode_id', 'cargo_type_id', 'origin_id', 'destination_id', 'service_job_type_id')
    def _compute_tariff_name(self):
        for rec in self.filtered(lambda tb: tb.tariff_for == 'job'):
            location_suffix = ''
            if rec.origin_id:
                location_suffix = '-{}'.format(rec.origin_id.loc_code)
            if rec.destination_id:
                location_suffix = '{}-{}'.format(location_suffix, rec.destination_id.loc_code)
            rec.tariff_name = '{}-{}{}'.format(
                rec.vendor_id.name or '',
                rec.service_job_type_id and str(rec.service_job_type_id.name).strip()[:2] or '',
                location_suffix
            )
        super()._compute_tariff_name()


class TariffBuyLine(models.Model):
    _inherit = 'tariff.buy.line'

    def get_charge_domain(self):
        self.ensure_one()
        if self.buy_tariff_id and self.buy_tariff_id.tariff_for == 'job':
            charge_category = self.env.ref('fm_service_job.job_charge_category', raise_if_not_found=False)
            return json.dumps(['|', ('company_id', '=', self.company_id.id), ('company_id', '=', False), ('categ_id', '=', charge_category.id)])
        else:
            return super().get_charge_domain()
