# -*- coding: utf-8 -*-
from . import models
from . import wizard

from odoo import api, SUPERUSER_ID


def _add_service_job_sequence(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Generate Quote-ServiceJob Company specific Sequence when there are multiple existing company
    FreightSequenceObj = env['freight.sequence'].sudo()
    CompanyObj = env['res.company'].sudo()
    for company in CompanyObj.search([]):
        sequences = FreightSequenceObj.search([
            ('company_id', '=', company.id), ('ir_model_id.model', 'in', ['shipment.quote']), ('freight_product_id', '!=', False),
        ])
        quote_company_sequence = env.ref('fm_service_job_quote.sequence_freight_service_job_quotation')
        if quote_company_sequence.company_id != company:
            quote_company_sequence = quote_company_sequence.copy({'company_id': company.id})
        if not sequences:
            vals = {
                'name': 'Service-Job Quote',
                'ir_model_id': env.ref('fm_quote.model_shipment_quote').id,
                'ir_field_id': env.ref('fm_quote.field_shipment_quote__name').id,
                'ir_sequence_id': quote_company_sequence.id,
                'freight_product_id': env.ref('fm_service_job_quote.service_job_freight_product').id,
                'sequence_format': "QT-{{str(object.service_job_type_id.name).replace(' ', '')[:2].upper()}}",
                'number_increment': 1,
                'padding': 5,
                'company_id': company.id
            }
            FreightSequenceObj.create(vals)
