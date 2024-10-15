# -*- coding: utf-8 -*-
from odoo import models


class FreightServiceJob(models.Model):
    _inherit = 'freight.service.job'

    def action_tariff_services_wizard(self, model):
        self.ensure_one()
        action = self.env.ref('fm_tariff.tariff_service_wizard_wizard_action').sudo().read()[0]
        vendors = self.service_job_partner_ids.filtered(lambda partner: partner.partner_type_id.is_vendor).mapped('partner_id')
        ctx = self._context.copy()
        wiz_tariff_service = self.env['tariff.service.wizard'].create({
            'service_job_id': self.id,
            'tariff_type': ctx.get('tariff_type', 'charge_master'),
            'origin_id': self.origin_un_location_id.id,
            'origin_port_id': self.origin_port_un_location_id.id,
            'destination_id': self.destination_un_location_id.id,
            'destination_port_id': self.destination_port_un_location_id.id,
            'company_id': self.company_id.id,
            'customer_id': self.client_id.id if ctx.get('tariff_type') == 'sell_tariff' else False,
            'vendor_ids': vendors and vendors.ids if ctx.get('tariff_type') == 'buy_tariff' else [],
            'sell_charge_master': True if model == 'service.job.charge.revenue' else False,
            'buy_charge_master': True if model == 'service.job.charge.cost' else False,
            'tariff_for': 'job',
            'service_job_type_id': self.service_job_type_id.id,
            'ignore_location': True,
        })
        wiz_tariff_service.action_fetch_tariff()
        action['name'] = '{}: Fetch from {}'.format(self.name, str(ctx.get('tariff_type')).replace('_', ' ').title())
        action['domain'] = [('id', '=', wiz_tariff_service.id)]
        action['res_id'] = wiz_tariff_service.id
        return action
