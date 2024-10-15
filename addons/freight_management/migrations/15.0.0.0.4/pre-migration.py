# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    doc_type_house_job_sheet = env.ref('freight_management.doc_type_house_job_sheet').id

    # Removing all house shipment document with type job cost
    query = f'DELETE FROM freight_house_shipment_document WHERE document_type_id = {doc_type_house_job_sheet}'
    cr.execute(query)

    # Removing all master shipment document with type job cost
    query = f'DELETE FROM freight_master_shipment_document WHERE document_type_id = {doc_type_house_job_sheet}'
    cr.execute(query)
