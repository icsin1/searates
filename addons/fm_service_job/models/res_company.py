# -*- coding: utf-8 -*-

from odoo import models


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _create_per_company_freight_sequence(self):
        super()._create_per_company_freight_sequence()
        company_sequence = self.env.ref('fm_service_job.sequence_freight_service_job')
        if company_sequence.company_id != self:
            company_sequence = company_sequence.copy({'company_id': self.id})
        FreightSequenceObj = self.env['freight.sequence']
        vals = {
            'name': 'Service Job',
            'ir_model_id': self.env.ref('fm_service_job.model_freight_service_job').id,
            'ir_field_id': self.env.ref('fm_service_job.field_freight_service_job__name').id,
            'ir_sequence_id': company_sequence.id,
            'sequence_format': 'SJ-',
            'number_increment': 1,
            'padding': 5,
            'company_id': self.id
        }
        FreightSequenceObj.create(vals)
