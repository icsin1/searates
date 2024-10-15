# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    mrt_docs = env['stimulsoft.mrt.report'].search([('json_spec_id', '!=', False)])
    for mrt_doc in mrt_docs:
        mrt_doc.json_spec_id.write({'json_type': 'document'})

    mrt_docs = env['stimulsoft.mrt.report.product'].search([('json_spec_id', '!=', False)])
    for mrt_doc in mrt_docs:
        mrt_doc.json_spec_id.write({'json_type': 'document'})
        mrt_doc.json_spec_id.dependency_spec_ids.mapped('property_specification_id').write({'json_type': 'document'})
        mrt_doc.product_id.write({'product_type': 'document'})
