from odoo import models, _


class PartnerOutstandingReportHandler(models.AbstractModel):
    _inherit = 'partner.outstanding.statement.report'

    def get_buttons(self, report, options, **kwargs):
        buttons = super().get_buttons(report, options, **kwargs)
        buttons.update({
            'pdf': [
                {
                    'name': _('Detailed with Ageing'),
                    'action': 'action_print_report_ageing_pdf',
                    'help': _('Download Detailed Report with Ageing Details'),
                    'context': {'detailed': True, 'ageing': True}
                },
                {
                    'name': _('Detailed without Ageing'),
                    'action': 'action_print_report_ageing_pdf',
                    'help': _('Download Detailed Report without Ageing Details'),
                    'context': {'detailed': True, 'ageing': False}
                }
            ]
        })
        return buttons

    def get_report_action(self, options=False):
        return self.env["ir.actions.actions"]._for_xml_id('customer_statement_report.fm_operation_reports_outstanding_customer_statement')

    def action_print_report_ageing_pdf(self, report, options, button_context, **kwargs):
        return self._get_print_report_pdf(report, options, **kwargs)

    def _get_print_report_pdf(self, report, options, **kwargs):
        context = dict(self._context)
        self = self.with_context(context)
        button_context = context.get('button_context', {})
        filename = report._get_report_filename(options)

        action = self.get_report_action(options)
        action.update({
            'data': {
                'print_report_name': filename,
                'report_model': action.get('report_res_model'),
                'report_res_id': action.get('report_res_id'),
                'model': report._name,
                'report_id': report.id,
                'options': options,
                'folded': not button_context.get('detailed', False),
                'show_ageing': button_context.get('ageing', False),
                'button_context': button_context
            }
        })
        action['context'] = {**self.env.context, 'active_ids': report.ids}
        return action

    def _get_section_ageing_data(self, report, records, options, current_partner_id=False, **kwargs):

        def _get_key_value(values, key):
            return values.get('main_group', {}).get('{}_original'.format(key))

        total_os_amount = sum([_get_key_value(line.get('values'), 'os_amount') for line in records if _get_key_value(line.get('values'), 'ageing') > 0])
        total_current_amount = sum([_get_key_value(line.get('values'), 'os_amount') for line in records if _get_key_value(line.get('values'), 'ageing') <= 0])
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
            ageing_sum = sum([_get_key_value(line.get('values'), 'os_amount') for line in records if _ageing_range_match(
                ageing_range[0], ageing_range[1], _get_key_value(line.get('values'), 'ageing')
            )])
            ageing_data[ageing_key] = (ageing_sum, self._format_currency(ageing_sum))

        return {
            'lines': records,
            'total_os_amount': (total_os_amount, self._format_currency(total_os_amount)),
            'total_current_amount': (total_current_amount, self._format_currency(total_current_amount)),
            'total_due_amount': (total_due_amount, self._format_currency(total_due_amount)),
            'ageing_data': ageing_data
        }

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
