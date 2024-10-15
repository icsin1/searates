# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    doc_types = env['freight.document.type'].search([('document_mode', '=', 'out'), ('report_template_id', '!=', False)])

    for doc_type in doc_types:
        doc_type.write({
            'report_template_ref_id': f'docx.template,{doc_type.report_template_id.id}'
        })
