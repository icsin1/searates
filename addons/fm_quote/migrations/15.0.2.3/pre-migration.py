# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    # Removing other document type (out mode)
    env = api.Environment(cr, SUPERUSER_ID, {})
    type_id = env.ref('fm_quote.doc_type_quote_other').id
    query = "DELETE FROM freight_quote_document where document_type_id = {}".format(type_id)
    cr.execute(query)
