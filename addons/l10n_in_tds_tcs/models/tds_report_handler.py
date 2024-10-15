from odoo import models


class TDSReportHandler(models.AbstractModel):
    _name = 'tds.report.handler'
    _inherit = 'mixin.report.handler'
    _description = 'TDS Report Handler'
    _override_sections_data = True
    _override_section_detail = True

    def _get_query_result(self, report, domain, options, **kwargs):
        tds_tax_report = self.env.ref('l10n_in_tds_tcs.india_tds_report', False)
        table, where, params = self.env[report.model_name]._where_calc(domain).get_sql()
        query = f"""
                SELECT atrltr.account_tax_report_line_id, ARRAY_AGG(DISTINCT CASE
                          WHEN account_move_line__move_id.state = 'posted'
                            AND account_move_line__move_id.company_id = {self.env.company.id}
                            AND {where}
                          THEN aataml.account_move_line_id
                          ELSE NULL
                          END) AS move_line_ids
                FROM account_tax_report_line atrl
                LEFT JOIN account_tax_report_line_tags_rel atrltr
                  ON atrl.id = atrltr.account_tax_report_line_id
                LEFT JOIN account_account_tag_account_move_line_rel aataml 
                  ON atrltr.account_account_tag_id = aataml.account_account_tag_id
                LEFT JOIN account_move_line
                  ON aataml.account_move_line_id = account_move_line.id
                LEFT JOIN account_move account_move_line__move_id
                  ON account_move_line.move_id = account_move_line__move_id.id
                WHERE atrl.report_id = {tds_tax_report.id}
                GROUP BY atrltr.account_tax_report_line_id;
        """
        self._cr.execute(query, [*params])
        return self._cr.dictfetchall()

    def _report_handler_tds_values(self, report, report_line, data_fields, options, current_group_by, **kwargs):
        section_records = self.get_tds_report_section_data(report, report_line, data_fields, options, current_group_by, **kwargs)
        # Formating records in section
        sections = report_line._groups_to_sections(section_records, current_group_by, options, **kwargs)
        return sections

    def _get_section_detail_data(self, report, section_line, options, parent, **kwargs):
        super()._get_section_detail_data(report, section_line, options, parent, **kwargs)
        group_by_fields = list(set(section_line.group_by_fields.split(',')) - set([parent.get('code')]))
        group_by = group_by_fields[0]
        return self._report_handler_tds_values(report, section_line, [], options, group_by, tax_report_line_id=parent.get('id'), **kwargs)

    def get_tds_report_section_data(self, report, report_line, data_fields, options, current_group_by, **kwargs):
        section_records = []
        filter_date_options = options.get('filter_date_options', {})
        group_date_from = filter_date_options.get('date_from')
        group_date_to = filter_date_options.get('date_to')
        date_field = report.date_field.name
        domain = [(date_field, '<=', group_date_to)]
        if filter_date_options.get('mode') == 'range':
            domain += [(date_field, '>=', group_date_from)]
        records = self._get_query_result(report, domain, options, **kwargs)

        if not kwargs.get('group_total') and current_group_by == 'id':
            move_line_ids = next((item['move_line_ids'] for item in records if item['account_tax_report_line_id'] == kwargs.get('tax_report_line_id', False)), [])
            move_line_ids = self.env[report.model_name].with_context(prefetch_fields=False).browse(list(filter(None, move_line_ids)))
            for line in move_line_ids:
                section_records.append({
                    'id': line.id,
                    'section': line.move_id.name,
                    'name': line.move_id.name,
                    'reference_number': line.move_id.ref,
                    'pan_number': line.move_id.partner_id.l10n_in_pan_number,
                    'deductee_name': line.move_id.partner_id.name,
                    'bill_date': line.move_id.invoice_date.strftime('%d/%m/%Y'),
                    'total_amount': line.tax_base_amount,
                    'tds_amount': abs(line.balance),
                    'tax_rate': abs(line.tax_line_id.amount),
                })
        else:
            # Grouping by TDS tax report line
            for record in records:
                tax_report_line_id = self.env['account.tax.report.line'].browse(record.get('account_tax_report_line_id', False))
                move_line_ids = self.env[report.model_name].with_context(prefetch_fields=False).browse(list(filter(None, record.get('move_line_ids'))))
                section_records.append({
                    'id': tax_report_line_id.id,
                    'section': tax_report_line_id.name or '',
                    'name': tax_report_line_id.name,
                    'reference_number': '',
                    'pan_number': '',
                    'deductee_name': '',
                    'bill_date': '',
                    'total_amount': abs(sum(move_line_ids.mapped('tax_base_amount'))) or 0.0,
                    'tds_amount': abs(sum(move_line_ids.mapped('balance'))) or 0.0,
                    'tax_rate': '',
                })
        return section_records
