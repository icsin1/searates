import logging
from odoo import models

_logger = logging.getLogger(__name__)


class GSTB2CSInvoiceReportHandler(models.AbstractModel):
    _name = 'gst.b2cs.invoice.report.handler'
    _description = 'B2C(Small) Details - 7'
    _inherit = ['gst.b2b.invoice.report.handler']

    def generate_csv_report(self, writer, data, record):
        writer.writeheader()
        report = data.get('report')
        options = data.get('options')
        kwargs = data.get('kwargs')

        tax_report_line_cess = self.env.ref('l10n_in.cess_group', False)

        DataModel = self.env[report.model_name]
        move_lines = DataModel.search(report._get_default_domain(options, **kwargs))

        group_taxes_lines = {ml.move_id.l10n_in_state_id: {} for ml in move_lines}
        for each_move_line in move_lines:
            tax_ids = each_move_line.mapped('tax_ids').filtered(
                lambda tax: tax_report_line_cess not in (tax.invoice_repartition_line_ids + tax.refund_repartition_line_ids).mapped('invoice_tax_id.tax_group_id')
            )
            for taxes in tax_ids:
                group_taxes_lines[each_move_line.move_id.l10n_in_state_id].setdefault(taxes, [])
                group_taxes_lines[each_move_line.move_id.l10n_in_state_id][taxes] += each_move_line
        for place_of_supply_id, value in group_taxes_lines.items():
            for tax_key, move_lines in value.items():
                move_lines = self.env['account.move.line'].concat(*list(move_lines))
                taxable_value = sum(move_lines.mapped('balance')) * -1
                cess_amount = 0.00
                for line in move_lines:
                    price_currency = line.currency_id._convert(abs(line.price_unit), line.company_currency_id, line.company_id, line.date)
                    taxes_data = self._compute_l10n_in_tax(line.tax_ids, abs(price_currency), line.company_currency_id, line.quantity, line.product_id, line.partner_id)
                    sign = 1 if line.move_id.move_type != 'out_refund' else -1
                    cess_amount += taxes_data['cess_amount'] * sign

                writer.writerow({
                    'Type': 'OE',
                    'Place Of Supply': '{}-{}'.format(place_of_supply_id.l10n_in_tin, place_of_supply_id.name),
                    'Applicable % of Tax Rate': '',
                    'Rate': sum(tax_key.children_tax_ids.mapped('amount')) if tax_key.amount_type == 'group' else tax_key.amount,
                    'Taxable Value': taxable_value,
                    'Cess Amount': cess_amount,
                    'E-Commerce GSTIN': '',
                })

    def get_csv_header(self):
        return [
            'Type',
            'Place Of Supply',
            'Rate',
            'Applicable % of Tax Rate',
            'Taxable Value',
            'Cess Amount',
            'E-Commerce GSTIN',
        ]
