import logging
import base64
from odoo import models, _
from odoo.addons.http_routing.models.ir_http import slugify

_logger = logging.getLogger(__name__)

try:
    import csv
except ImportError:
    _logger.debug("Can not import csvwriter`.")


class GSTB2BInvoiceReportHandler(models.AbstractModel):
    _name = 'gst.b2b.invoice.report.handler'
    _description = 'B2B Invoice - 4A, 4B, 4C, 6B, 6C Handler'
    _inherit = ['mixin.report.handler', 'report.report_csv.abstract']
    _hide_title = True

    def get_buttons(self, report, options, **kwargs):
        buttons = super().get_buttons(report, options, **kwargs)
        buttons.update({'csv': [{
            'name': _("CSV"),
            'action': "action_generate_csv_format",
            'primary': False
        }]})
        return buttons

    def _get_voucher_type(self, move):
        invoice_type_selection = {
            'out_invoice': _('Invoice'),
            'out_receipt': _('Invoice'),
            'out_refund': _('Credit Note'),
            }
        return invoice_type_selection[move.move_type]

    def _process_values(self, move, values, options, **kwargs):
        return values

    def _get_sections(self, report, options, **kwargs):
        sections = []

        DataModel = self.env[report.model_name]

        report_groups = options.get('report_header_groups', {})
        for report_group_key, report_group in report_groups.items():
            records = DataModel.search(report_group.get('__domain', [])).mapped('move_id')
            for move in records:
                tax_amount_data_dict = {'igst_amount': 0.0, 'sgst_amount': 0.0, 'cgst_amount': 0.0, 'cess_amount': 0.0}
                for line in move.invoice_line_ids:
                    price_currency = line.currency_id._convert(abs(line.price_unit), line.company_currency_id, line.company_id, line.date)
                    taxes_data = self._compute_l10n_in_tax(line.tax_ids, abs(price_currency), line.company_currency_id, line.quantity, line.product_id, line.partner_id)
                    tax_amount_data_dict['igst_amount'] += taxes_data['igst_amount']
                    tax_amount_data_dict['cgst_amount'] += taxes_data['cgst_amount']
                    tax_amount_data_dict['sgst_amount'] += taxes_data['sgst_amount']
                    tax_amount_data_dict['cess_amount'] += taxes_data['cess_amount']

                total_tax_amount = sum(list(tax_amount_data_dict.values()))

                move_values = self._generate_values(report, self._process_values(move, {
                    'number': move.name,
                    'customer': move.partner_id.name,
                    'gst_number': move.partner_id.vat,
                    'invoice_date': move.invoice_date,
                    'voucher_type': self._get_voucher_type(move),
                    'taxable_value': abs(move.amount_untaxed_signed),
                    'total_cgst': tax_amount_data_dict['cgst_amount'],
                    'total_sgst': tax_amount_data_dict['sgst_amount'],
                    'total_igst': tax_amount_data_dict['igst_amount'],
                    'total_cess': tax_amount_data_dict['cess_amount'],
                    'total_tax': total_tax_amount,
                    'invoice_total': abs(move.amount_total_signed)
                }, options, tax_data=tax_amount_data_dict, **kwargs))

                sections.append(self._generate_section({
                    'action': self._get_action(move),
                    'values': {report_group_key: move_values}
                }))
        return sections

    def _get_action(self, move):
        return {}

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

    # ------------------------------ #
    #          CSV REPORT            #
    # ------------------------------ #

    def _get_objs_for_report(self, docids, data):
        # OVERRIDING EXCEL Object browser
        return self

    def get_invoice_type(self):
        return {
            'regular': 'Regular B2B',
            'special_economic_zone_with_payment': 'SEZ supplies with payment',
            'special_economic_zone_without_payment': 'SEZ supplies without payment',
            'deemed_export': 'Deemed Exp',
            'composition': 'Regular B2B'
        }

    def generate_csv_report(self, writer, data, record):
        writer.writeheader()
        report = data.get('report')
        options = data.get('options')
        kwargs = data.get('kwargs')

        tax_report_line_cess = self.env.ref('l10n_in.cess_group', False)

        DataModel = self.env[report.model_name]
        move_lines = DataModel.search(report._get_default_domain(options, **kwargs))
        for move in move_lines.mapped('move_id'):
            tax_ids = move.line_ids.mapped('tax_ids').filtered(
                lambda tax: tax_report_line_cess not in (tax.invoice_repartition_line_ids + tax.refund_repartition_line_ids).mapped('invoice_tax_id.tax_group_id')
            )
            for tax in tax_ids:
                tax_lines = move.line_ids.filtered(lambda line: tax in line.tax_ids)
                gst_treatment = move.l10n_in_gst_treatment if move.l10n_in_gst_treatment != 'special_economic_zone' else \
                    '{}_{}'.format(move.l10n_in_gst_treatment, move.l10n_in_export_type)

                taxable_value = abs(sum(tax_lines.mapped('balance')))

                cess_amount = 0
                for tax_line in tax_lines:
                    price_currency = tax_line.currency_id._convert(abs(tax_line.price_unit), tax_line.company_currency_id, tax_line.company_id, tax_line.date)
                    taxes_data = self._compute_l10n_in_tax(
                        tax_line.tax_ids, price_currency, tax_line.company_currency_id, tax_line.quantity, tax_line.product_id, tax_line.partner_id
                    )
                    cess_amount += taxes_data.get('cess_amount', 0)

                writer.writerow({
                    'GSTIN/UIN of Recipient': move.partner_id.vat,
                    'Receiver Name': move.partner_id.name,
                    'Invoice Number': move.name,
                    'Invoice date': move.invoice_date.strftime('%d-%b-%y'),
                    'Invoice Value': abs(move.amount_total_signed),
                    'Place Of Supply': '{}-{}'.format(move.l10n_in_state_id.l10n_in_tin, move.l10n_in_state_id.name),
                    'Reverse Charge': 'Y' if tax.l10n_in_reverse_charge else 'N',
                    'Applicable % of Tax Rate': '',
                    'Invoice Type': self.get_invoice_type().get(gst_treatment, ''),
                    'E-Commerce GSTIN': '',
                    'Rate': sum(tax.children_tax_ids.mapped('amount')) if tax.amount_type == 'group' else tax.amount,
                    'Taxable Value': taxable_value,
                    'Cess Amount': abs(cess_amount)
                })

    def get_csv_header(self):
        return [
            'GSTIN/UIN of Recipient',
            'Receiver Name',
            'Invoice Number',
            'Invoice date',
            'Invoice Value',
            'Place Of Supply',
            'Reverse Charge',
            'Applicable % of Tax Rate',
            'Invoice Type',
            'E-Commerce GSTIN',
            'Rate',
            'Taxable Value',
            'Cess Amount'
        ]

    def csv_report_options(self):
        res = super().csv_report_options()
        res['fieldnames'] += self.get_csv_header()
        res['delimiter'] = ','
        res['quoting'] = csv.QUOTE_ALL
        return res

    def action_generate_csv_format(self, report, options, button_context, **kwargs):
        csv_file, extension = self.create_csv_report(self.ids, {
            'options': options,
            'kwargs': kwargs,
            'report': report
        })
        title = report.get_title()
        filename = '{}.{}'.format(slugify(title), extension)

        report.write({
            'report_export_filename': filename,
            'report_export_content': base64.b64encode(csv_file.encode('utf-8'))
        })
        url = '/web/content/%s/%s/%s/%s' % (report._name, report.id, 'report_export_content', report.report_export_filename)
        return {'type': 'ir.actions.act_url', 'url': url}
