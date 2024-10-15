# -*- coding: utf-8 -*-
import json
from odoo import models, fields


class Opportunity(models.Model):
    _inherit = "crm.prospect.opportunity"

    def get_loading_port_domain(self):
        self.ensure_one()
        if self.opportunity_for == 'job':
            domain = []
            if self.origin_country_id:
                domain.append(('country_id', '=', self.origin_country_id.id))
            return json.dumps(domain)
        else:
            return super().get_loading_port_domain()

    def get_discharge_port_domain(self):
        self.ensure_one()
        if self.opportunity_for == 'job':
            domain = []
            if self.destination_country_id:
                domain.append(('country_id', '=', self.destination_country_id.id))
            return json.dumps(domain)
        else:
            return super().get_discharge_port_domain()

    opportunity_for = fields.Selection(selection_add=[('job', 'Service Job')])
    service_job_type_id = fields.Many2one('freight.job.type', ondelete='restrict')

    def _prepare_quotation_vals(self):
        self.ensure_one()
        quote_vals = super()._prepare_quotation_vals()
        quote_vals.update({'default_service_job_type_id': self.service_job_type_id.id})
        return quote_vals
