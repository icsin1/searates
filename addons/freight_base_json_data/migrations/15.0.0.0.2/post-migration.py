# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    json_specs = env['product.json.specification'].search([('freight_product_id', '!=', False)])
    for json_spec in json_specs:
        json_spec.write({'product_domain': json_spec.freight_product_id.match_domain})
        json_spec._compute_dependency_spec_ids()
