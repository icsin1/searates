# -*- coding: utf-8 -*-
from . import models
from . import wizard
from . import controllers


from odoo import api, SUPERUSER_ID


def _add_service_job_sequence(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Generate ServiceJob Company specific Sequence when there are multiple existing company
    FreightSequenceObj = env['freight.sequence'].sudo()
    CompanyObj = env['res.company'].sudo()
    for company in CompanyObj.search([]):
        sequences = FreightSequenceObj.search([
            ('company_id', '=', company.id), ('ir_model_id.model', 'in', ['freight.service.job'])
        ])
        company_sequence = env.ref('fm_service_job.sequence_freight_service_job')
        if company_sequence.company_id != company:
            company_sequence = company_sequence.copy({'company_id': company.id})
        if not sequences:
            vals = {
                'name': 'Service Job',
                'ir_model_id': env.ref('fm_service_job.model_freight_service_job').id,
                'ir_field_id': env.ref('fm_service_job.field_freight_service_job__name').id,
                'ir_sequence_id': company_sequence.id,
                'sequence_format': 'SJ-',
                'number_increment': 1,
                'padding': 5,
                'company_id': company.id
            }
            FreightSequenceObj.create(vals)
