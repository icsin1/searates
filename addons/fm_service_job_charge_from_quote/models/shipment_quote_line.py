# -*- coding: utf-8 -*-
from odoo import fields, models


class ShipmentQuoteLine(models.Model):
    _inherit = "shipment.quote.line"

    service_job_id = fields.Many2one('freight.service.job', copy=False)
    service_job_cost_charge_id = fields.Many2one('service.job.charge.cost', copy=False)
    service_job_revenue_charge_id = fields.Many2one('service.job.charge.revenue', copy=False)
    service_cost_charge_ids = fields.Many2many('service.job.charge.cost', 'service_job_charge_cost_shipment_quote_line_rel', 'shipment_quote_line_id',
                                               'service_job_charge_cost_id', copy=False)
    service_revenue_charge_ids = fields.Many2many('service.job.charge.revenue', 'service_job_charge_revenue_shipment_quote_line_rel', 'shipment_quote_line_id',
                                                  'service_job_charge_revenue_id', copy=False)
