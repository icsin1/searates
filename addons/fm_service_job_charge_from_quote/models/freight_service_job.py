# -*- coding: utf-8 -*-

from odoo import models, api


class FreightServiceJob(models.Model):
    _inherit = 'freight.service.job'

    @api.model_create_single
    def create(self, values):
        service_job = super().create(values)
        # auto fetch services from quote to service_job
        if service_job.service_job_quote_id:
            service_job.action_fetch_quote_services()
        return service_job

    def update_cost_charge_ids(self):
        self.ensure_one()
        service_cost_charge_ids = self.env['service.job.charge.cost'].search([('service_job_id', '=', self.id)])
        ServiceJobCostChargeObj = self.env['service.job.charge.cost']
        for quote_charge in self.service_job_quote_id.quotation_line_ids.filtered(
                lambda ql: not ql.service_cost_charge_ids if self.service_job_quote_id.shipment_count == 'single'
                else ql.service_cost_charge_ids not in service_cost_charge_ids and ql.service_cost_charge_ids.product_id.ids not in service_cost_charge_ids.product_id.ids):
            vals = quote_charge._prepare_charges_cost_value()
            vals.update({'service_job_id': self.id})
            service_job_charge = ServiceJobCostChargeObj.create(vals)
            quote_charge.service_cost_charge_ids = service_job_charge | quote_charge.mapped('service_cost_charge_ids')

    def update_revenue_charge_ids(self):
        self.ensure_one()
        service_revenue_charge_ids = self.env['service.job.charge.revenue'].search([('service_job_id', '=', self.id)])
        ServiceJobRevenueChargeObj = self.env['service.job.charge.revenue']
        for quote_charge in self.service_job_quote_id.quotation_line_ids.filtered(
                lambda ql: not ql.service_revenue_charge_ids if self.service_job_quote_id.shipment_count == 'single'
                else ql.service_revenue_charge_ids not in service_revenue_charge_ids and ql.product_id.id not in service_revenue_charge_ids.product_id.ids):
            vals = quote_charge._prepare_charges_revenue_value()
            vals.update({'service_job_id': self.id})
            service_job_charge = ServiceJobRevenueChargeObj.create(vals)
            quote_charge.service_revenue_charge_ids = service_job_charge | quote_charge.mapped('service_revenue_charge_ids')

    def action_fetch_quote_services(self):
        self.ensure_one()
        self.update_cost_charge_ids()
        self.update_revenue_charge_ids()
