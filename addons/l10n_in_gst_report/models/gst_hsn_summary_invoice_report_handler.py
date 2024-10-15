import logging
import base64
import json
import ast
from collections import defaultdict
from odoo import models, _
from odoo.addons.http_routing.models.ir_http import slugify

_logger = logging.getLogger(__name__)

try:
    import csv
except ImportError:
    _logger.debug("Can not import csvwriter`.")


class GSTHSNSummaryInvoiceReportHandler(models.AbstractModel):
    _name = 'gst.hsn.summary.invoice.report.handler'
    _description = 'HSN Summary Handler'
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

    def _compute_l10n_in_tax(self, taxes, price_unit, currency=None, quantity=1.0, product=None, partner=None):
        """common method to compute gst tax amount base on tax group"""
        res = {'igst_amount': 0.0, 'sgst_amount': 0.0, 'cgst_amount': 0.0, 'cess_amount': 0.0, 'tax_rate': 0.0}
        AccountTaxRepartitionLine = self.env['account.tax.repartition.line']
        tax_report_lines = {
            'igst': self.env.ref('l10n_in.tax_report_line_igst', False),
            'cgst': self.env.ref('l10n_in.tax_report_line_cgst', False),
            'sgst': self.env.ref('l10n_in.tax_report_line_sgst', False),
            'cess': self.env.ref('l10n_in.tax_report_line_cess', False),
        }
        filter_tax = taxes.filtered(lambda t: t.type_tax_use != 'none')
        res['tax_rate'] = sum(filter_tax.mapped('amount'))
        tax_compute = filter_tax.compute_all(price_unit, currency=currency, quantity=quantity, product=product, partner=partner)

        for tax_data in tax_compute['taxes']:
            tax_report_line = AccountTaxRepartitionLine.browse(tax_data['tax_repartition_line_id']).mapped('tag_ids.tax_report_line_ids')
            for key, value in tax_report_lines.items():
                if value in tax_report_line:
                    res[f"{key}_amount"] += tax_data['amount']
        res.update(tax_compute)
        return res

    def _group_move_lines(self, move_lines):
        grouped_lines = defaultdict(lambda: defaultdict(lambda: self.env['account.move.line']))
        cess_tax_group = self.env.ref('l10n_in.cess_group')
        for line in move_lines:
            tax_rate = 0
            for tax in line.tax_ids.filtered(lambda tax: tax.tax_group_id.id != cess_tax_group.id):
                if tax.amount_type == 'group':
                    tax_rate = sum(tax.children_tax_ids.mapped('amount'))
                else:
                    tax_rate = tax.amount

            key = (
                line.product_id.l10n_in_hsn_code,  # hsn code
                line.product_id.l10n_in_hsn_description,  # hsn description
                line.product_id.uom_id.l10n_in_code if line.product_id.detailed_type != 'service' else '',  # uom code
                str(tax_rate)  # tax rate
            )
            grouped_lines[key]['move_line_ids'] |= line
        return grouped_lines

    def _compute_tax_amount(self, move_lines):
        tax_amount_data_dict = {'taxable_value': 0.0, 'sgst_amount': 0.0, 'igst_amount': 0.0, 'cgst_amount': 0.0, 'cess_amount': 0.0, 'tax_rate': 0.0}
        tax_lines = self.env['account.move.line']
        cess_tax_group = self.env.ref('l10n_in.cess_group')

        for tax in move_lines.mapped('tax_ids'):
            tax_lines |= move_lines.filtered(lambda line: tax in line.tax_ids and tax.tax_group_id.id != cess_tax_group.id)

        for tax_line in tax_lines:
            tax_amount_data_dict['taxable_value'] += abs(sum(tax_line.mapped('balance')))

            price_currency = tax_line.currency_id._convert(tax_line.price_unit, tax_line.company_currency_id, tax_line.company_id, tax_line.date)
            price_currency = price_currency if tax_line.balance < 0.0 else -price_currency
            taxes_data = self._compute_l10n_in_tax(
                tax_line.tax_ids, price_currency, tax_line.company_currency_id, tax_line.quantity, tax_line.product_id, tax_line.partner_id
            )
            tax_amount_data_dict['cess_amount'] += taxes_data.get('cess_amount', 0)
            tax_amount_data_dict['igst_amount'] += taxes_data.get('igst_amount', 0)
            tax_amount_data_dict['cgst_amount'] += taxes_data.get('cgst_amount', 0)
            tax_amount_data_dict['sgst_amount'] += taxes_data.get('sgst_amount', 0)

        for product_tax in move_lines.mapped('product_id.taxes_id'):
            if product_tax.amount_type == 'group':
                tax_amount_data_dict['tax_rate'] += sum(product_tax.children_tax_ids.mapped('amount'))
            else:
                tax_amount_data_dict['tax_rate'] += product_tax.amount
        return tax_amount_data_dict

    def _get_sections(self, report, options, **kwargs):
        sections = []

        DataModel = self.env[report.model_name]
        report_groups = options.get('report_header_groups', {})
        for report_group_key, report_group in report_groups.items():
            move_lines = DataModel.search(report_group.get('__domain', []))
            grouped_lines = self._group_move_lines(move_lines)

            for hsn_data, move_line_ids in grouped_lines.items():
                hsn_code, hsn_description, uom_code, tax_rate = hsn_data
                move_lines = list(move_line_ids.values())[0]
                tax_amount_data_dict = self._compute_tax_amount(move_lines)

                total_amount = sum([
                    tax_amount_data_dict['taxable_value'],
                    tax_amount_data_dict['cgst_amount'],
                    tax_amount_data_dict['sgst_amount'],
                    tax_amount_data_dict['igst_amount'],
                    tax_amount_data_dict['cess_amount']
                ])

                move_values = self._generate_values(report, {
                    'hsn_code': hsn_code,
                    'uqc': uom_code and uom_code.split('-')[0],
                    'description': hsn_description or '',
                    'taxable_value': tax_amount_data_dict['taxable_value'] or 0.0,
                    'total_cgst': tax_amount_data_dict.get('cgst_amount') or 0.0,
                    'total_sgst': tax_amount_data_dict.get('sgst_amount') or 0.0,
                    'total_igst': tax_amount_data_dict.get('igst_amount') or 0.0,
                    'total_cess': tax_amount_data_dict.get('cess_amount') or 0.0,
                    'total_tax': abs(total_amount) - tax_amount_data_dict['taxable_value'] or 0.0,
                    'quantity': sum(move_lines.filtered(lambda line: line.product_id.detailed_type != 'service').mapped('quantity')) or 0.0,
                    'tax_rate': tax_rate or 0,
                    'invoice_total': abs(total_amount) or 0.0,
                })

                sections.append(self._generate_section({
                    'id': '_'.join([val for val in hsn_data if val]),
                    'values': {report_group_key: move_values},
                    'title_key': 'hsn_code',
                    'action': self._get_action(move_lines),
                }))

        return sections

    def _get_action(self, move_lines):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "l10n_in_gst_report.action_l10n_in_report_gstr1_hsn_code_details"
        )
        context = ast.literal_eval(action.get('context', "{}"))
        context.update({"domain": [("id", "in", move_lines.ids)]})
        action['context'] = json.dumps(context)
        return action

    def get_csv_header(self):
        return [
            'HSN',
            'Description',
            'UQC',
            'Total Quantity',
            'Total Value',
            'Taxable Value',
            'Integrated Tax Amount',
            'Central Tax Amount',
            'State/UT Tax Amount',
            'Cess Amount',
            'Rate'
        ]

    # ------------------------------ #
    #          CSV REPORT            #
    # ------------------------------ #

    def _get_objs_for_report(self, docids, data):
        # OVERRIDING EXCEL Object browser
        return self

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

    def generate_csv_report(self, writer, data, record):
        writer.writeheader()
        report = data.get('report')
        options = data.get('options')
        kwargs = data.get('kwargs')
        DataModel = self.env[report.model_name]

        move_lines = DataModel.search(report._get_default_domain(options, **kwargs))
        grouped_lines = self._group_move_lines(move_lines)

        for hsn_data, move_line_ids in grouped_lines.items():
            move_lines = list(move_line_ids.values())[0]
            hsn_code, hsn_description, uom_code, tax_rate = hsn_data
            tax_amount_data_dict = self._compute_tax_amount(move_lines)

            total_amount = sum([
                tax_amount_data_dict['taxable_value'],
                tax_amount_data_dict['cgst_amount'],
                tax_amount_data_dict['sgst_amount'],
                tax_amount_data_dict['igst_amount'],
                tax_amount_data_dict['cess_amount']
            ])

            writer.writerow({
                'HSN': hsn_code,
                'Description': hsn_description or '',
                'UQC': uom_code and uom_code.split('-')[0] or '',
                'Total Quantity': sum(move_lines.filtered(lambda line: line.product_id.detailed_type != 'service').mapped('quantity')) or 0.0,
                'Total Value': abs(total_amount) or 0,
                'Taxable Value': tax_amount_data_dict['taxable_value'],
                'Integrated Tax Amount': tax_amount_data_dict['igst_amount'],
                'Central Tax Amount': tax_amount_data_dict['cgst_amount'],
                'State/UT Tax Amount': tax_amount_data_dict['sgst_amount'],
                'Cess Amount': tax_amount_data_dict['cess_amount'],
                'Rate': tax_rate or 0
            })
