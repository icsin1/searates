# -*- coding: utf-8 -*-
from . import models

from odoo import api, SUPERUSER_ID


def _account_l10n_in_post_init(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    tax_groups = {
        env.ref('l10n_in.sgst_group'): env.ref('l10n_in_base.sgst_base_tag_tax'),
        env.ref('l10n_in.cgst_group'): env.ref('l10n_in_base.cgst_base_tag_tax'),
        env.ref('l10n_in.igst_group'): env.ref('l10n_in_base.igst_base_tag_tax'),
        env.ref('l10n_in.cess_group'): env.ref('l10n_in_base.cess_base_tag_tax')
    }

    for tax_group, tax_grid in tax_groups.items():
        taxes = env['account.tax'].search([
            ('country_id.code', '=', 'IN'),
            ('amount_type', '!=', 'group'),
            ('tax_group_id', '=', tax_group.id)
        ])

        invoice_repartition_line_ids_base = taxes.invoice_repartition_line_ids.filtered(lambda ln: ln.repartition_type == 'base')
        refund_repartition_line_ids_base = taxes.refund_repartition_line_ids.filtered(lambda ln: ln.repartition_type == 'base')

        invoice_repartition_line_ids_base.write({'tag_ids': [(4, tax_grid.id, False)]})
        refund_repartition_line_ids_base.write({'tag_ids': [(4, tax_grid.id, False)]})
