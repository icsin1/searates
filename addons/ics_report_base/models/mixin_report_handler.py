from odoo import models
from odoo.tools.misc import formatLang


class BaseReportHandler(models.AbstractModel):
    _name = 'mixin.report.handler'
    _description = 'Report Handler Mixin'
    _hide_title = False
    _override_section_detail = False
    _override_sections_data = False

    def __init__(self, pool, cr):
        super().__init__(pool, cr)

    def _get_report_filename(self, report, options, **kwargs):
        return report.get_title()

    def _get_report_title(self, report):
        return report.name

    def _get_column_label(self, column, options, **kwargs):
        return column.name

    def _get_filter_options(self, filter, options, **kwargs):
        return {}

    def _get_filter_label(self, report_filter, options, **kwargs):
        return report_filter.get_name(options.get('dynamic_filter_search', {}).get(report_filter.filter_key))

    def _get_handler_buttons(self, report, options, **kwargs):
        buttons = self.get_buttons(report, options, **kwargs)
        for button_type, button_list in buttons.items():
            for button in button_list:
                button.update({'mode': 'handler'})
            buttons.update({button_type: button_list})
        return buttons

    def get_buttons(self, report, options, **kwargs):
        return {}

    def _get_sections(self, report, options, **kwargs):
        return []

    def _format_currency(self, amount, currency=None):
        return formatLang(self.env, amount, currency_obj=currency or self.env.company.currency_id)

    def _generate_section(self, section):
        return {
            'level': 1,
            'title': '',
            'children': [],
            'report_line_id': False,
            **section
        }

    def _parse_display_value(self, section_values, column, value, variables={}, **kwargs):
        Expression = self.env['mixin.base.report.expression']
        if kwargs.get('report_line') and column:
            report_line = kwargs.get('report_line')
            expression_label = report_line.expression_ids.filtered(lambda expr: expr.name == column.expression_label)
            if expression_label:
                Expression = expression_label[0]

        ttype = column.value_type
        parse_value = '_parse_field_{}'.format(ttype)
        if hasattr(Expression, parse_value):
            return getattr(Expression, parse_value)(section_values, value, None, variables)
        return value

    def _generate_values(self, report, section_values, report_line=None, **kwargs):
        values = {}
        columns = report.column_ids
        for key, value in section_values.items():
            column = columns.filtered(lambda col: col.expression_label == key)
            values.update({
                key: self._parse_display_value(section_values, column, value, section_values, report_line=report_line),
                f'{key}_is_zero': bool(value in ['', 0, None]),
                f'{key}_original': value
            })
        return values

    def _get_handler_domain(self, report, options, **kwargs):
        return []

    def get_report_action(self, options=False):
        return self.env["ir.actions.actions"]._for_xml_id("ics_report_base.action_generic_web_report_pdf")

    def get_title(self, report, options, **kwargs):
        return report.get_title()

    def _get_section_detail_data(self, report, section_line, options, parent, **kwargs):
        return []

    def _post_process_sections(self, report, report_line, sections, options, **kwargs):
        return sections
