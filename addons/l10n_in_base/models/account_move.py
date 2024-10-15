# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_in_transaction_mode = fields.Selection([
        ('inter_state', 'Inter State'),
        ('intra_state', 'Intra State')
    ], readonly=True, string='Transaction Mode')

    l10n_in_export_type = fields.Selection([
        ('with_payment', 'With Payment'),
        ('without_payment', 'Without Payment')
    ], default='without_payment', string="Payment Type")

    def _post(self, soft=True):
        posted = super()._post(soft)

        for move in posted.filtered(lambda m: m.country_code == 'IN'):
            company_unit_partner = move.journal_id.l10n_in_gstin_partner_id or move.journal_id.company_id
            move.l10n_in_transaction_mode = ('inter_state', 'intra_state')[move.l10n_in_state_id == company_unit_partner.state_id]

        return posted

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = super()._onchange_partner_id()
        self.l10n_in_state_id = False
        if self.partner_id and self.country_code == 'IN':
            if self.journal_id.type == 'sale':
                country_code = self.partner_id.country_id.code
                self.l10n_in_state_id = self.partner_id.state_id if country_code == 'IN' else self.env.ref('l10n_in.state_in_ot', raise_if_not_found=False)
            elif self.journal_id.type == 'purchase':
                self.l10n_in_state_id = self.company_id.state_id
        return res

    @api.depends('partner_id')
    def _compute_l10n_in_gst_treatment(self):
        super()._compute_l10n_in_gst_treatment()
        for record in self:
            if not record.l10n_in_gst_treatment and record.move_type in ['out_receipt', 'in_receipt']:
                record.l10n_in_gst_treatment = 'unregistered'

    def _compute_l10n_in_tax(self, taxes, price_unit, currency=None, quantity=1.0, product=None, partner=None):
        """common method to compute gst tax amount base on tax group"""
        res = {'igst_amount': 0.0, 'sgst_amount': 0.0, 'cgst_amount': 0.0, 'cess_amount': 0.0, 'tax_rate': 0.0}
        AccountTaxRepartitionLine = self.env['account.tax.repartition.line']
        tax_report_line_igst = self.env.ref('l10n_in.tax_report_line_igst', False)
        tax_report_line_cgst = self.env.ref('l10n_in.tax_report_line_cgst', False)
        tax_report_line_sgst = self.env.ref('l10n_in.tax_report_line_sgst', False)
        tax_report_line_cess = self.env.ref('l10n_in.tax_report_line_cess', False)
        filter_tax = taxes.filtered(lambda t: t.type_tax_use != 'none')
        res['tax_rate'] = sum(filter_tax.mapped('amount'))
        tax_compute = filter_tax.compute_all(price_unit, currency=currency, quantity=quantity, product=product, partner=partner)
        for tax_data in tax_compute['taxes']:
            tax_report_lines = AccountTaxRepartitionLine.browse(tax_data['tax_repartition_line_id']).mapped('tag_ids.tax_report_line_ids')
            if tax_report_line_sgst in tax_report_lines:
                res['sgst_amount'] += tax_data['amount']
            if tax_report_line_cgst in tax_report_lines:
                res['cgst_amount'] += tax_data['amount']
            if tax_report_line_igst in tax_report_lines:
                res['igst_amount'] += tax_data['amount']
            if tax_report_line_cess in tax_report_lines:
                res['cess_amount'] += tax_data['amount']
        res.update(tax_compute)
        return res

    def _l10n_in_get_hsn_summary_table(self):
        has_igst = False
        has_gst = False
        has_cess = False
        self.ensure_one()
        display_uom = self.env.user.user_has_groups('uom.group_uom')
        tax_report_line_cess = self.env.ref('l10n_in.cess_group', False)
        lines_by_taxes_and_product = {}
        items = []
        for line in self.invoice_line_ids:
            taxes_key = tuple(line.tax_ids.ids)
            product_key = line.product_id.l10n_in_hsn_code
            if display_uom:
                key = (taxes_key, product_key, line.product_uom_id.name)
            else:
                key = (taxes_key, product_key)
            # Group lines by taxes and product
            lines_by_taxes_and_product.setdefault(key, []).append(line)
        for key, move_lines in lines_by_taxes_and_product.items():
            tax_amount_data_dict = {'igst_amount': 0.0, 'sgst_amount': 0.0, 'cgst_amount': 0.0, 'cess_amount': 0.0, 'taxable_value': 0.0}
            quantity = 0
            rate = 0
            counter = 0
            for line in move_lines:
                if not counter:
                    tax_ids = line.mapped('tax_ids').filtered(
                        lambda tax: tax_report_line_cess not in (tax.invoice_repartition_line_ids + tax.refund_repartition_line_ids).mapped('invoice_tax_id.tax_group_id')
                    )
                    for tax in tax_ids:
                        rate += sum(tax.children_tax_ids.mapped('amount')) if tax.amount_type == 'group' else tax.amount
                    counter = 1
                taxes_data = self._compute_l10n_in_tax(line.tax_ids, line.price_unit, line.company_currency_id, line.quantity, line.product_id, line.partner_id)
                vat_amount = line.price_total - line.price_subtotal
                amount_currency_untaxed = line.price_total - vat_amount
                tax_amount_data_dict['igst_amount'] += taxes_data['igst_amount']
                tax_amount_data_dict['cgst_amount'] += taxes_data['cgst_amount']
                tax_amount_data_dict['sgst_amount'] += taxes_data['sgst_amount']
                tax_amount_data_dict['cess_amount'] += taxes_data['cess_amount']
                tax_amount_data_dict['taxable_value'] += amount_currency_untaxed
                quantity += line.quantity
            if tax_amount_data_dict.get('cgst_amount') or tax_amount_data_dict.get('sgst_amount'):
                has_gst = True
            if tax_amount_data_dict.get('igst_amount'):
                has_igst = True
            if tax_amount_data_dict.get('cess_amount'):
                has_cess = True
            items.append({
                'l10n_in_hsn_code': key[1],
                'quantity': quantity,
                'rate': rate,
                'amount_untaxed': tax_amount_data_dict['taxable_value'],
                'tax_amount_cgst': tax_amount_data_dict['cgst_amount'],
                'tax_amount_sgst': tax_amount_data_dict['sgst_amount'],
                'tax_amount_igst': tax_amount_data_dict['igst_amount'],
                'tax_amount_cess': tax_amount_data_dict['cess_amount'],
                'uom': key[2] if len(key) == 3 else False
            })
        nb_columns = 5
        if has_igst:
            nb_columns += 1
        if has_gst:
            nb_columns += 2
        if has_cess:
            nb_columns += 1
        return {
            'has_igst': has_igst,
            'has_gst': has_gst,
            'has_cess': has_cess,
            'nb_columns': nb_columns,
            'display_uom': display_uom,
            'items': items,
        }


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _get_l10n_in_hsn_code(self):
        self.ensure_one()
        return False
