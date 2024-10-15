# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ServiceJobChargeCost(models.Model):
    _inherit = 'service.job.charge.cost'

    buy_tariff_line_id = fields.Many2one('tariff.buy.line')

    @api.model
    def action_tariff_services_wizard(self, service_job_id):
        service_job = self.env['freight.service.job'].browse(int(service_job_id))
        return service_job.action_tariff_services_wizard(model=self._name)
