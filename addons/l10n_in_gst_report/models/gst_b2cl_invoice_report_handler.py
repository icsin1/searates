import logging
from odoo import models

_logger = logging.getLogger(__name__)


class GSTB2CLInvoiceReportHandler(models.AbstractModel):
    _name = 'gst.b2cl.invoice.report.handler'
    _description = 'B2C(Large) Invoice - 5A, 5B Handler'
    _inherit = ['gst.b2b.invoice.report.handler']

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
                taxable_value = abs(sum(tax_lines.mapped('balance')))

                cess_amount = 0
                for tax_line in tax_lines:
                    price_currency = tax_line.currency_id._convert(abs(tax_line.price_unit), tax_line.company_currency_id, tax_line.company_id, tax_line.date)
                    taxes_data = self._compute_l10n_in_tax(
                        tax_line.tax_ids, abs(price_currency), tax_line.company_currency_id, tax_line.quantity, tax_line.product_id, tax_line.partner_id
                    )
                    cess_amount += taxes_data.get('cess_amount', 0)

                writer.writerow({
                    'Invoice Number': move.name,
                    'Invoice date': move.invoice_date.strftime('%d-%b-%y'),
                    'Invoice Value': move.amount_total_signed,
                    'Place Of Supply': '{}-{}'.format(move.l10n_in_state_id.l10n_in_tin, move.l10n_in_state_id.name),
                    'Applicable % of Tax Rate': '',
                    'Rate': sum(tax.children_tax_ids.mapped('amount')) if tax.amount_type == 'group' else tax.amount,
                    'Taxable Value': taxable_value,
                    'Cess Amount': cess_amount,
                    'E-Commerce GSTIN': '',
                })

    def get_csv_header(self):
        return [
            'Invoice Number',
            'Invoice date',
            'Invoice Value',
            'Place Of Supply',
            'Applicable % of Tax Rate',
            'Rate',
            'Taxable Value',
            'Cess Amount',
            'E-Commerce GSTIN',
        ]
