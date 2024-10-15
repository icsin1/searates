import ast
from odoo import models, fields, api


class VATReturnPurchaseLine(models.Model):
    _name = "vat.return.purchase.line"
    _description = "Vat Return Purchase Line"

    vat_return_id = fields.Many2one('vat.return', string='Vat Return ID')
    description = fields.Char('Description')
    box_no = fields.Char('Box')
    base_amount = fields.Float('Base Amount', default=0.0)
    tax_amount = fields.Float('Tax Amount', default=0.0)
    credit_amount = fields.Float('Credit Amount', default=0.0)
    debit_amount = fields.Float('Debit Amount', default=0.0)
    adjustment_amount = fields.Float(string='Adjustment Amount', default=0.0)
    actual_base_amount = fields.Float(string='Actual Base Amount', compute="_compute_vat_amount", store=True)
    actual_tax_amount = fields.Float(string='Actual Tax Amount', compute="_compute_tax_amount", store=True)
    tag_ids = fields.Many2many('account.account.tag', string='Tag ids')

    @api.depends('base_amount', 'credit_amount')
    def _compute_vat_amount(self):
        for record in self:
            record.actual_base_amount = record.base_amount - record.credit_amount

    @api.depends('tax_amount', 'debit_amount')
    def _compute_tax_amount(self):
        for record in self:
            record.actual_tax_amount = record.tax_amount - record.debit_amount

    def action_view_detail_report(self):
        domain = [
            ('date', '>=', self.vat_return_id.from_date), ('date', '<=', self.vat_return_id.to_date),
            ('parent_state', '=', 'posted'),
            ('tax_tag_ids', 'in', self.tag_ids.ids), ('exclude_from_invoice_tab', '=', False),
            ('company_id', '=', self.env.company.id)
        ]
        if self.vat_return_id.partner_ids:
            domain.append(('partner_id', 'in', self.vat_return_id.partner_ids.ids))
        action = self.env["ir.actions.actions"]._for_xml_id("l10n_ae_vat_return.action_l10n_ae_report_vat_root")
        context = ast.literal_eval(action.get('context', '{}'))
        context.update({'domain': domain})
        action['context'] = context
        return action
