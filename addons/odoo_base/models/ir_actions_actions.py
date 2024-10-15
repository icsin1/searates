import logging
import traceback
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval


_logger = logging.getLogger(__name__)


class IrActionsActions(models.Model):
    _inherit = 'ir.actions.actions'

    # Field override to make Generic Action-Help message
    help = fields.Html(compute='_get_default_message', store=True)

    # Added fake depends field to make this field store True
    @api.depends('name')
    def _get_default_message(self):
        for action in self:
            action.help = """
                <p class='o_view_nocontent_smiling_face'>No records available!</p>
                """

    @api.model
    def get_bindings(self, model_name):
        # Super-Call Binding After Cleaning cache to load refreshed view when accessing same model view
        self.clear_caches()
        res = super().get_bindings(model_name)

        # Feature: Report Action Title dynamic
        reports = res.get('report') or []
        context = self._context.copy()
        ReportActionObj = self.env['ir.actions.report'].sudo()
        filtered_reports = []
        for report in reports:
            report_action = False
            if report.get('id'):
                report_action_domain = [('visibility', '!=', False), ('id', '=', int(report.get('id')))]
                report_action = ReportActionObj.search(report_action_domain, limit=1)
            if report_action:
                if self._match_visibility_rule(report_action.visibility, context):
                    report_name_res = report_action._get_dynamic_report_label(context)
                    report['name'] = report_name_res
                    filtered_reports.append(report)
            else:
                filtered_reports.append(report)
        res['report'] = filtered_reports
        return res

    def _match_visibility_rule(self, visibility, dict_to_compare):
        '''
        visibility: type:python-expression - Python condition defined in the report action
        dict_to_compare: type:dictionary - context value to compare with visibility value
        '''
        matching_result = False
        try:
            matching_result = True if safe_eval(visibility, dict_to_compare) else False
        except Exception:
            traceback_msg = traceback.format_exc()
            _logger.warning(traceback_msg)
        return matching_result

    def _get_dynamic_report_label(self, dict_to_compare):
        self.ensure_one()
        report_label = self.name
        try:
            report_label = [report_label.name for report_label in self.report_label_ids.sorted(key="sequence") if self._match_visibility_rule(report_label.visibility, dict_to_compare)]
            report_label = report_label[0] if report_label else self.name
        except Exception:
            traceback_msg = traceback.format_exc()
            _logger.error('Error occurred in Dynamic Report Labelling: %s-%s', traceback_msg)
            report_label = self.name
        return report_label
