# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ServiceJobChargeRevenue(models.Model):
    _inherit = 'service.job.charge.revenue'

    sell_tariff_line_id = fields.Many2one('tariff.sell.line')

    @api.model
    def action_tariff_services_wizard(self, service_job_id):
        service_job = self.env['freight.service.job'].browse(int(service_job_id))
        return service_job.action_tariff_services_wizard(model=self._name)
