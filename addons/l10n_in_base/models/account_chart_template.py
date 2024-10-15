# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class AccountChartTemplate(models.Model):
    _inherit = 'account.chart.template'

    def _update_base_tax_grid(self, company):
        tax_groups = {
            self.env.ref('l10n_in.sgst_group'): self.env.ref('l10n_in_base.sgst_base_tag_tax'),
            self.env.ref('l10n_in.cgst_group'): self.env.ref('l10n_in_base.cgst_base_tag_tax'),
            self.env.ref('l10n_in.igst_group'): self.env.ref('l10n_in_base.igst_base_tag_tax'),
            self.env.ref('l10n_in.cess_group'): self.env.ref('l10n_in_base.cess_base_tag_tax')
        }

        for tax_group, tax_grid in tax_groups.items():
            taxes = self.env['account.tax'].search([
                ('company_id', '=', company.id),
                ('country_id.code', '=', 'IN'),
                ('amount_type', '!=', 'group'),
                ('tax_group_id', '=', tax_group.id)
            ])

            invoice_repartition_line_ids_base = taxes.invoice_repartition_line_ids.filtered(lambda ln: ln.repartition_type == 'base')
            refund_repartition_line_ids_base = taxes.refund_repartition_line_ids.filtered(lambda ln: ln.repartition_type == 'base')

            invoice_repartition_line_ids_base.write({'tag_ids': [(4, tax_grid.id, False)]})
            refund_repartition_line_ids_base.write({'tag_ids': [(4, tax_grid.id, False)]})

    def _load(self, sale_tax_rate, purchase_tax_rate, company):
        """ Set tax calculation rounding method required in Chilean localization"""
        res = super()._load(sale_tax_rate, purchase_tax_rate, company)
        if company.country_id.code == 'IN':
            self._update_base_tax_grid(company)
        return res
