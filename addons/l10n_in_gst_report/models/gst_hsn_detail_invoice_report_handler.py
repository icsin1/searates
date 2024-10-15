import logging
import base64
from odoo import models, _
from odoo.addons.http_routing.models.ir_http import slugify

_logger = logging.getLogger(__name__)

try:
    import csv
except ImportError:
    _logger.debug("Can not import csvwriter`.")


class GSTHSNCodeDetailInvoiceReportHandler(models.AbstractModel):
    _name = 'gst.hsn.code.detail.invoice.report.handler'
    _description = 'HSN Code Detail Handler'
    _inherit = ['mixin.report.handler', 'report.report_csv.abstract']
    _hide_title = True

    def _get_sections(self, report, options, **kwargs):
        sections = []

        DataModel = self.env[report.model_name]

        report_groups = options.get('report_header_groups', {})
        for report_group_key, report_group in report_groups.items():
            move_lines = DataModel.search(report_group.get('__domain', []))
            for move_line in move_lines:
                move_id = move_line.mapped('move_id')
                tax_amount_data_dict = {'igst_amount': 0.0, 'sgst_amount': 0.0, 'cgst_amount': 0.0, 'cess_amount': 0.0, 'taxable_value': 0.0}
                price_currency = move_line.currency_id._convert(abs(move_line.price_unit), move_line.company_currency_id, move_line.company_id, move_line.date)
                taxes_data = self._compute_l10n_in_tax(move_line.tax_ids, abs(price_currency), move_line.company_currency_id, move_line.quantity, move_line.product_id, move_line.partner_id)
                tax_amount_data_dict['igst_amount'] += taxes_data['igst_amount']
                tax_amount_data_dict['cgst_amount'] += taxes_data['cgst_amount']
                tax_amount_data_dict['sgst_amount'] += taxes_data['sgst_amount']
                tax_amount_data_dict['cess_amount'] += taxes_data['cess_amount']
                tax_amount_data_dict['taxable_value'] += abs(sum(move_line.mapped('balance')))

                total_amount = sum(list(tax_amount_data_dict.values()))

                product_id = move_lines.mapped('product_id')[0]
                uqc = product_id.uom_id.l10n_in_code.split('-')[0] if product_id.detailed_type != 'service' else ''
                quantity = (line.quantity if line.product_id.detailed_type != 'service' else 0 for line in move_lines)

                move_values = self._generate_values(report, {
                    'invoice_date': move_id.invoice_date,
                    'customer': move_id.partner_id.name,
                    'voucher_type': self._get_voucher_type(move_id),
                    'voucher_num': move_id.name,
                    'uqc': uqc,
                    'quantity': sum(quantity),
                    'invoice_total': abs(total_amount),
                    'taxable_value': tax_amount_data_dict['taxable_value'],
                    'total_cgst': tax_amount_data_dict['cgst_amount'],
                    'total_sgst': tax_amount_data_dict['sgst_amount'],
                    'total_igst': tax_amount_data_dict['igst_amount'],
                    'total_cess': tax_amount_data_dict['cess_amount'],
                    'total_tax': abs(total_amount) - tax_amount_data_dict['taxable_value'],
                })

                sections.append(self._generate_section({
                    'values': {report_group_key: move_values},
                    'title_key': 'voucher_num',
                    'action': self._get_action(move_id),
                    'id': move_id.id,
                }))
        return sections

    def _get_action(self, move):
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        form_view = [(self.env.ref('account.view_move_form').id, 'form')]
        action['views'] = form_view + [(state, view) for state, view in action.get('views', []) if view != 'form']
        action['res_id'] = move.id
        return action

    def _get_voucher_type(self, move):
        invoice_type_selection = {
            'out_invoice': _('Invoice'),
            'out_receipt': _('Invoice'),
            'out_refund': _('Credit Note'),
            }
        return invoice_type_selection[move.move_type]

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
