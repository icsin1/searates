from odoo import models, fields, api


class AccountAccount(models.Model):
    _inherit = 'account.account'

    exclude_from_aged_reports = fields.Boolean(default=False)

    is_sale_tax_account = fields.Boolean(compute='_compute_is_sale_tax', store=True)
    is_purchase_tax_account = fields.Boolean(compute='_compute_is_purchase_tax', store=True)

    @api.depends('company_id', 'company_id.account_sale_tax_id')
    def _compute_is_sale_tax(self):
        for rec in self:
            account_sale_tax = rec.company_id.account_sale_tax_id
            invoice_tax_lines = account_sale_tax.invoice_repartition_line_ids
            refund_tax_lines = account_sale_tax.refund_repartition_line_ids
            rec.is_sale_tax_account = rec.id in invoice_tax_lines.account_id.ids or rec.id in refund_tax_lines.account_id.ids

    @api.depends('company_id', 'company_id.account_purchase_tax_id')
    def _compute_is_purchase_tax(self):
        for rec in self:
            account_purchase_tax = rec.company_id.account_purchase_tax_id
            invoice_tax_lines = account_purchase_tax.invoice_repartition_line_ids
            refund_tax_lines = account_purchase_tax.refund_repartition_line_ids
            rec.is_purchase_tax_account = rec.id in invoice_tax_lines.account_id.ids or rec.id in refund_tax_lines.account_id.ids
