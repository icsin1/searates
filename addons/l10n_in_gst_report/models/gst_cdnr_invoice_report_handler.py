from odoo import models, _


class GSTCDNRInvoiceReportHandler(models.AbstractModel):
    _name = 'gst.cdnr.invoice.report.handler'
    _description = 'Credit/Debit Notes (Registered)(9B)'
    _inherit = ['gst.b2b.invoice.report.handler']

    def _get_voucher_type(self, move):
        return _('Credit Note') if move.move_type in ['out_refund'] else super()._get_voucher_type(move)

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
                gst_treatment = move.l10n_in_gst_treatment if move.l10n_in_gst_treatment != 'special_economic_zone' else \
                    '{}_{}'.format(move.l10n_in_gst_treatment, move.l10n_in_export_type)
                writer.writerow({
                    'GSTIN/UIN of Recipient': move.partner_id.vat,
                    'Receiver Name': move.partner_id.name,
                    'Note Number': move.name,
                    'Note date': move.invoice_date.strftime('%d-%b-%y'),
                    'Note Type': 'C',
                    'Place Of Supply': '{}-{}'.format(move.l10n_in_state_id.l10n_in_tin, move.l10n_in_state_id.name),
                    'Note Supply Type': self.get_invoice_type().get(gst_treatment, ''),
                    'Note Value': abs(move.amount_total_signed),
                    'Reverse Charge': 'Y' if tax.l10n_in_reverse_charge else 'N',
                    'Applicable % of Tax Rate': '',
                    'Rate': sum(tax.children_tax_ids.mapped('amount')) if tax.amount_type == 'group' else tax.amount,
                    'Taxable Value': taxable_value,
                    'Cess Amount': abs(cess_amount)
                })

    def get_csv_header(self):
        return [
            'GSTIN/UIN of Recipient',
            'Receiver Name',
            'Note Number',
            'Note date',
            'Note Type',
            'Place Of Supply',
            'Reverse Charge',
            'Note Supply Type',
            'Note Value',
            'Applicable % of Tax Rate',
            'Rate',
            'Taxable Value',
            'Cess Amount'
        ]
