from odoo import models, tools


class WebReportHandlerMixin(models.AbstractModel):
    _inherit = 'mixin.report.handler'

    @tools.ormcache('str(record)', 'str(domain)', 'str(kwargs)')
    def _report_handler_opening_closing_balance(self, report, report_line, record, domain, options, report_group, group_by, **kwargs):

        if not report_line.compute_opening_and_closing_balance:
            return {
                'opening_balance': 0,
                'closing_balance': 0,
            }

        current_group_by = kwargs.get('current_group_by')
        date_field = report.date_field.name

        group_period = report_group.get('group_period')

        date_from = group_period.get('date_from')
        date_to = group_period.get('date_to')

        closing_groups = []
        opening_groups = []

        if group_by:
            group_domain = []
            if group_by != 'id':
                group_by_value = record.get(group_by)
                if isinstance(group_by_value, tuple):
                    group_by_value = group_by_value[0]
                group_domain = [(group_by, '=', group_by_value)]
            elif current_group_by:
                group_by_value = record.get(current_group_by)
                if isinstance(group_by_value, tuple):
                    group_by_value = group_by_value[0]
                group_domain = [(current_group_by, '=', group_by_value)]

            # Finding Opening Balance

            if group_by != 'id':
                initial_domain = report._generate_initial_balance_domain(date_from, date_to, options, **kwargs) + group_domain
                opening_groups = self.env[report.model_name].sudo().read_group(initial_domain, ['balance'], [group_by] if group_by and group_by != 'id' else [])

            # Finding Closing Balance
            group_period = report_group.get('group_period')
            closing_domain = report._get_default_domain(options, ignore_date_domain=True, **kwargs) + group_domain
            closing_domain += [(date_field, '<=', record.get(date_field, date_to))]

            closing_groups = self.env[report.model_name].sudo().read_group(closing_domain, ['balance'], [group_by] if group_by and group_by != 'id' else [])

            return {
                'opening_balance': opening_groups and opening_groups[0].get('balance', 0) or 0,
                'closing_balance': closing_groups and closing_groups[0].get('balance', 0) or 0,
            }

        if kwargs.get('group_total') and not current_group_by:

            init_group_domain = [(date_field, '<', date_from)]
            opening_domain = report._get_default_domain(options, ignore_date_domain=True, **kwargs) + init_group_domain
            opening_groups = self.env[report.model_name].sudo().read_group(opening_domain, ['balance'], [group_by] if group_by and group_by != 'id' else [])

            group_domain = [(date_field, '<=', date_to)]
            closing_domain = report._get_default_domain(options, ignore_date_domain=True, **kwargs) + group_domain
            closing_groups = self.env[report.model_name].sudo().read_group(closing_domain, ['balance'], [group_by] if group_by and group_by != 'id' else [])

        return {
            'opening_balance': opening_groups and opening_groups[0].get('balance', 0) or 0,
            'closing_balance': closing_groups and closing_groups[0].get('balance', 0) or 0
        }
