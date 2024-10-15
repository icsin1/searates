from odoo import models


class GSTNILRatedInvoiceReportHandler(models.AbstractModel):
    _name = 'gst.nil.invoice.report.handler'
    _description = 'Nil Rated Supplies(8A, 8B, 8C, 8D)'
    _inherit = ['gst.b2b.invoice.report.handler']

    def _get_sections(self, report, options, **kwargs):
        sections = []

        DataModel = self.env[report.model_name]

        report_groups = options.get('report_header_groups', {})
        for report_group_key, report_group in report_groups.items():
            records = DataModel.search(report_group.get('__domain', [])).mapped('move_id')
            for move in records:
                taxes_data = self._compute_nil_rated_taxes(move.invoice_line_ids)

                move_values = self._generate_values(report, self._process_values(move, {
                    'number': move.name,
                    'customer': move.partner_id.name,
                    'invoice_date': move.invoice_date,
                    'voucher_type': self._get_voucher_type(move),
                    'taxable_value': abs(move.amount_untaxed_signed),
                    'invoice_total': abs(move.amount_total_signed),
                    'total_nil_rated': taxes_data.get('nil_rated_amount', 0),
                    'total_exempt': taxes_data.get('exempt_amount', 0),
                    'total_non_gst': taxes_data.get('non_gst_amount', 0)
                }, options, tax_data=taxes_data, **kwargs))

                sections.append(self._generate_section({
                    'action': self._get_action(move),
                    'values': {report_group_key: move_values}
                }))
        return sections

    def _compute_nil_rated_taxes(self, move_lines):

        tax_amount_data_dict = {'nil_rated_amount': 0.0, 'exempt_amount': 0.0, 'non_gst_amount': 0.0}
        tax_report_line_nil_rated = self.env.ref('l10n_in.tax_report_line_nil_rated', False)
        tax_report_line_exempt = self.env.ref('l10n_in.tax_report_line_exempt', False)
        tax_report_line_non_gst_supplies = self.env.ref('l10n_in.tax_report_line_non_gst_supplies', False)

        for line in move_lines:
            sign = -1
            tax_report_lines = line.tax_tag_ids.tax_report_line_ids
            if tax_report_line_nil_rated in tax_report_lines:
                tax_amount_data_dict['nil_rated_amount'] += (line.balance * sign)
            if tax_report_line_exempt in tax_report_lines:
                tax_amount_data_dict['exempt_amount'] += (line.balance * sign)
            if tax_report_line_non_gst_supplies in tax_report_lines:
                tax_amount_data_dict['non_gst_amount'] += (line.balance * sign)
        return tax_amount_data_dict

    def _get_csv_line(self, report, mode, gst_treatments, options, **kwargs):
        DataModel = self.env[report.model_name]
        domain = report._get_default_domain(options, **kwargs) + [('move_id.l10n_in_transaction_mode', '=', mode), ('move_id.l10n_in_gst_treatment', 'in', gst_treatments)]
        return self._compute_nil_rated_taxes(DataModel.search(domain))

    def generate_csv_report(self, writer, data, record):

        writer.writeheader()
        report = data.get('report')
        options = data.get('options')
        kwargs = data.get('kwargs')

        registered_gst_treatments = ['regular', 'special_economic_zone', 'deemed_export', 'composition']
        unregister_gst_treatments = ['consumer', 'unregistered']

        # Inter/Intra-State supplies for Register
        inter_state_registered = self._get_csv_line(report, 'inter_state', registered_gst_treatments, options, **kwargs)

        writer.writerow({
            'Description': 'Inter-State supplies to registered persons',
            'Nil Rated Supplies': inter_state_registered.get('nil_rated_amount', 0),
            'Exempted(other than nil rated/non GST supply)': inter_state_registered.get('exempt_amount', 0),
            'Non-GST Supplies': inter_state_registered.get('non_gst_amount', 0)
        })

        intra_state_registered = self._get_csv_line(report, 'intra_state', registered_gst_treatments, options, **kwargs)
        writer.writerow({
            'Description': 'Intra-State supplies to registered persons',
            'Nil Rated Supplies': intra_state_registered.get('nil_rated_amount', 0),
            'Exempted(other than nil rated/non GST supply)': intra_state_registered.get('exempt_amount', 0),
            'Non-GST Supplies': intra_state_registered.get('non_gst_amount', 0)
        })

        # Inter/Intra-State supplies for Unregistered
        inter_state_unregistered = self._get_csv_line(report, 'inter_state', unregister_gst_treatments, options, **kwargs)
        writer.writerow({
            'Description': 'Inter-State supplies to unregistered persons',
            'Nil Rated Supplies': inter_state_unregistered.get('nil_rated_amount', 0),
            'Exempted(other than nil rated/non GST supply)': inter_state_unregistered.get('exempt_amount', 0),
            'Non-GST Supplies': inter_state_unregistered.get('non_gst_amount', 0)
        })
        intra_state_unregistered = self._get_csv_line(report, 'intra_state', unregister_gst_treatments, options, **kwargs)
        writer.writerow({
            'Description': 'Intra-State supplies to unregistered persons',
            'Nil Rated Supplies': intra_state_unregistered.get('nil_rated_amount', 0),
            'Exempted(other than nil rated/non GST supply)': intra_state_unregistered.get('exempt_amount', 0),
            'Non-GST Supplies': intra_state_unregistered.get('non_gst_amount', 0)
        })

    def get_csv_header(self):
        return [
            'Description',
            'Nil Rated Supplies',
            'Exempted(other than nil rated/non GST supply)',
            'Non-GST Supplies'
        ]
