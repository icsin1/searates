from odoo import models, fields


class WebReportLine(models.Model):
    _inherit = 'web.report.line'

    is_account_report = fields.Boolean(related='web_report_id.is_account_report', store=True)
    compute_opening_and_closing_balance = fields.Boolean(default=False, string='Opening/Closing Balance')

    def _get_group_data(self, data_fields, domain, group_by, sub_group_by, options, **kwargs):
        if self.model_name == 'account.move.line':
            domain += [('display_type', 'not in', ('line_section', 'line_note'))]
        if self.is_account_report:
            if group_by == 'id':
                kwargs['order_by'] = self.web_report_id.date_field.name
        return super()._get_group_data(data_fields, domain, group_by, sub_group_by, options, **kwargs)
