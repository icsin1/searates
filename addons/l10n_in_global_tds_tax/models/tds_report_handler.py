from odoo import models


class TDSReportHandler(models.AbstractModel):
    _inherit = 'tds.report.handler'

    def get_tds_report_section_data(self, report, report_line, data_fields, options, current_group_by, **kwargs):
        section_records = super().get_tds_report_section_data(report, report_line, data_fields, options, current_group_by, **kwargs)
        filter_date_options = options.get('filter_date_options', {})
        group_date_from = filter_date_options.get('date_from')
        group_date_to = filter_date_options.get('date_to')
        date_field = report.date_field.name
        date_domain = [(date_field, '<=', group_date_to)]
        if filter_date_options.get('mode') == 'range':
            date_domain += [(date_field, '>=', group_date_from)]

        if not kwargs.get('group_total') and current_group_by == 'id':
            tax_report_line_id = self.env['account.tax.report.line'].browse(kwargs.get('tax_report_line_id', False))
            move_ids = self.env['account.move'].with_context(prefetch_fields=False).search(date_domain + [
                ('tds_tax_misc_move_id', '!=', False), ('tds_tax_misc_move_id.state', '=', 'posted')])
            # Filter the moves based on the tag_ids
            filtered_moves = move_ids.filtered(lambda move: any(
                tag_id in move.tds_tax_id.mapped('invoice_repartition_line_ids.tag_ids').ids +
                move.tds_tax_id.mapped('refund_repartition_line_ids.tag_ids').ids
                for tag_id in tax_report_line_id.tag_ids.ids
            ))
            for move in filtered_moves:
                section_records.append({
                    'id': move.line_ids[0].id,
                    'section': move.name,
                    'name': move.name,
                    'reference_number': move.ref,
                    'pan_number': move.partner_id.l10n_in_pan_number,
                    'deductee_name': move.partner_id.name,
                    'bill_date': move.invoice_date.strftime('%d/%m/%Y'),
                    'total_amount': abs(move.amount_untaxed_signed),
                    'tds_amount': abs(move.global_tds_tax_total_amount),
                    'tax_rate': abs(move.tds_tax_id.amount)
                })
        else:
            # Grouping by TDS tax report line
            move_ids = self.env['account.move'].with_context(prefetch_fields=False).search(date_domain + [
                ('tds_tax_misc_move_id', '!=', False), ('move_type', 'in', ('in_invoice', 'in_refund')), ('tds_tax_misc_move_id.state', '=', 'posted')])
            for record in section_records:
                tax_report_line_id = self.env['account.tax.report.line'].browse(record.get('id'))
                filtered_moves = move_ids.filtered(lambda move: any(
                    tag_id in move.tds_tax_id.mapped('invoice_repartition_line_ids.tag_ids').ids +
                    move.tds_tax_id.mapped('refund_repartition_line_ids.tag_ids').ids for tag_id in tax_report_line_id.tag_ids.ids))

                total_amount = record['total_amount'] + abs(sum(filtered_moves.mapped('amount_untaxed_signed')))
                tds_amount = record['tds_amount'] + abs(sum(filtered_moves.mapped('global_tds_tax_total_amount')))
                record.update({'total_amount': total_amount, 'tds_amount': tds_amount})

        return section_records
