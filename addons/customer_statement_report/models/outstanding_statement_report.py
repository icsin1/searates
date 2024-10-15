import json
from odoo import models, _


class OutstandingStatementReport(models.Model):
    _inherit = 'outstanding.statement.report'

    def _get_partners(self, options, **kwargs):
        """ Getting all partners for generating individual partner wise report
        """
        return self._get_sections(options, **kwargs)

    def get_report_action(self, options):
        action = super().get_report_action(options)
        context = self.env.context
        if self._name == 'outstanding.statement.report' and context.get('summary'):
            return self.env.ref('ics_account_reports.action_generic_report_account')
        elif self._name == 'outstanding.statement.report':
            self = self.with_context(landscape=False)
            return self.env.ref('customer_statement_report.fm_operation_reports_outstanding_customer_statement')
        return action

    def action_outstanding_customer_statement_with_aging(self, options, **kwargs):
        context = dict(self._context.get('context'))
        self = self.with_context(context)
        filename = self.get_report_filename(options)
        return {
            'type': 'ir_actions_account_report_download',
            'data': {
                'report_name': filename,
                'output_format': 'pdf',
                'model': self._name,
                'report_id': self.id,
                'options': json.dumps(options),
                'context': json.dumps(context),
                'show_ageing': True
            },
        }

    def action_outstanding_customer_statement_without_aging(self, options, **kwargs):
        context = dict(self._context.get('context'))
        self = self.with_context(context)
        filename = self.get_report_filename(options)
        return {
            'type': 'ir_actions_account_report_download',
            'data': {
                'report_name': filename,
                'output_format': 'pdf',
                'model': self._name,
                'report_id': self.id,
                'options': json.dumps(options),
                'context': json.dumps(context),
            },
        }

    def _get_buttons(self, options, **kwargs):
        """
        Override for add PDF with Aging and PDF without Aging report in dropdown
        """
        return [
            {
                'name': "PDF",
                'primary': True,
                'more': [
                    {
                        'action': "action_print_report_pdf_summary",
                        'name': 'Summary'
                    },
                    {
                        'action': "action_outstanding_customer_statement_with_aging",
                        'name': 'Detailed PDF with Aging'
                    },
                    {
                        'action': "action_outstanding_customer_statement_without_aging",
                        'name': "Detailed PDF without Aging",
                    }
                ]
            },
            {
                'name': "Excel",
                'primary': True,
                'more': [
                    {
                        'action': "action_print_report_xlsx_summary",
                        'name': 'Summary'
                    },
                    {
                        'action': "action_print_report_xlsx_detailed",
                        'name': "Detailed",
                    }
                ]
            },
            {
                'action': "action_print_report_send_mail",
                'name': "Send by Email",
            }
        ]

    def get_account_report_section_data_on_report(self, parent, options, current_partner_id=False, **kwargs):
        home_currency_code = self.env.company.currency_id.name
        records = self.get_account_report_section_data({'id': current_partner_id}, options, **kwargs)

        records = list(filter(lambda line: line.get('due_date'), records))

        total_os_amount = sum([line.get('values').get(f'O/S Amount {home_currency_code}')[0] for line in records if line.get('values').get('Ageing') > 0])
        total_current_amount = sum([line.get('values').get(f'O/S Amount {home_currency_code}')[0] for line in records if line.get('values').get('Ageing') <= 0])
        total_due_amount = total_os_amount + total_current_amount

        ageing_headers = self._get_ageing_headers(options)
        ageing_data = {}

        def _ageing_range_match(range_from, range_to, ageing):
            if range_from == 0 and ageing <= range_to:
                return True
            elif range_to == 0 and ageing >= range_from:
                return True
            elif range_from <= ageing <= range_to:
                return True
            return False
        for ageing_key, ageing_range in ageing_headers:
            ageing_sum = sum([line.get('values').get(f'O/S Amount {home_currency_code}')[0] for line in records if _ageing_range_match(
                ageing_range[0], ageing_range[1], line.get('values').get('Ageing')
            )])
            ageing_data[ageing_key] = (ageing_sum, self._format_currency(ageing_sum))

        section_data = {
            'lines': records,
            'total_os_amount': (total_os_amount, self._format_currency(total_os_amount)),
            'total_current_amount': (total_current_amount, self._format_currency(total_current_amount)),
            'total_due_amount': (total_due_amount, self._format_currency(total_due_amount)),
            'ageing_data': ageing_data
        }
        return section_data

    def _get_ageing_headers(self, options):
        return [
            (_("1 - 30"), (1, 30)),
            (_("31 - 60"), (31, 60)),
            (_("61 - 90"), (61, 90)),
            (_("91 - 120"), (91, 120)),
            (_("121 - 150"), (121, 150)),
            (_("151 - 180"), (151, 180)),
            (_("181+"), (181, 0)),
        ]
