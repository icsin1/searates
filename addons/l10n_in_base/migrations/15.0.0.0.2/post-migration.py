# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    tax_groups = [
        env.ref('l10n_in.sgst_group').id,
        env.ref('l10n_in.cgst_group').id,
        env.ref('l10n_in.igst_group').id,
        env.ref('l10n_in.cess_group').id
    ]
    taxes = env['account.tax'].search([
        ('country_id.code', '=', 'IN'),
        ('amount_type', '!=', 'group'),
        ('tax_group_id', 'in', tax_groups)
    ])
    for tax in taxes:
        invoice_repartition_line_ids_tax = tax.invoice_repartition_line_ids.filtered(
            lambda ln: ln.repartition_type == 'tax' and len(ln.tag_ids) != 0)
        refund_repartition_line_ids_tax = tax.refund_repartition_line_ids.filtered(
            lambda ln: ln.repartition_type == 'tax' and len(ln.tag_ids) != 0)
        if len(invoice_repartition_line_ids_tax) == 1 and len(refund_repartition_line_ids_tax) == 1:
            refund_repartition_line_ids_tax.write({'account_id': invoice_repartition_line_ids_tax.account_id.id})
