from odoo import models


class GSTEXPINInvoiceReportHandler(models.AbstractModel):
    _name = 'gst.expin.invoice.report.handler'
    _description = 'Export Invoices(6A)'
    _inherit = ['gst.b2b.invoice.report.handler']

    def _process_values(self, move, values, options, **kwargs):
        values = super()._process_values(move, values, options, **kwargs)
        values.update({
            'shipping_bill_no': move.l10n_in_shipping_bill_number,
            'shipping_bill_date': move.l10n_in_shipping_bill_date,
            'port_code': move.l10n_in_shipping_port_code_id and move.l10n_in_shipping_port_code_id.code or '',
        })
        return values

    def generate_csv_report(self, writer, data, record):
        writer.writeheader()
        report = data.get('report')
        options = data.get('options')
        kwargs = data.get('kwargs')

        tax_report_line_exclude = self.env.ref('l10n_in.cess_group', False)

        DataModel = self.env[report.model_name]
        move_lines = DataModel.search(report._get_default_domain(options, **kwargs))
        for move in move_lines.mapped('move_id'):
            tax_ids = move.line_ids.mapped('tax_ids').filtered(
                lambda tax: all([
                    tax_rep_line not in (tax.invoice_repartition_line_ids + tax.refund_repartition_line_ids).mapped('invoice_tax_id.tax_group_id') for tax_rep_line in tax_report_line_exclude
                ])
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
                    'Export Type': dict(move._fields['l10n_in_export_type'].selection).get(move.l10n_in_export_type) if move.l10n_in_gst_treatment == 'overseas' else 'B2CL',
                    'Invoice Number': move.name,
                    'Invoice Date': move.invoice_date.strftime('%d-%b-%y'),
                    'Invoice Value': abs(move.amount_total_signed),
                    'Port Code': move.l10n_in_shipping_port_code_id and move.l10n_in_shipping_port_code_id.code or '',
                    'Shipping Bill Number': move.l10n_in_shipping_bill_number and move.l10n_in_shipping_bill_number or '',
                    'Shipping Bill Date': move.l10n_in_shipping_bill_date and move.l10n_in_shipping_bill_date.strftime('%d-%b-%y') or '',
                    'Rate': sum(tax.children_tax_ids.mapped('amount')) if tax.amount_type == 'group' else tax.amount,
                    'Taxable Value': taxable_value,
                    'Cess Amount': abs(cess_amount)
                })

    def get_csv_header(self):
        return [
            'Export Type',
            'Invoice Number',
            'Invoice Date',
            'Invoice Value',
            'Port Code',
            'Shipping Bill Number',
            'Shipping Bill Date',
            'Rate',
            'Taxable Value',
            'Cess Amount'
        ]
