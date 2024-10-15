/** @odoo-module **/

import { patch } from 'web.utils';
import ActionReportViewer from 'odoo_web.action_report_viewer';
import StimulsoftViewer from 'base_document_reports_stimulsoft.viewer';


patch(ActionReportViewer.prototype, 'StimulsoftActionReportViewer', {
    view_report: async function (report_output_type, has_repeat_count) {
        let _super = this._super;
        var output_engine = this.options.context._report_engine || this.render_action.output_type;
        if (this.report_type != 'mrt' || output_engine != 'html') {
            return _super.apply(this, arguments);
        }
        // Processing .mrt action
        const record_data = await this.parent.rpc({
            route: '/web/action/report/read_record',
            params: {
                action_id: this.action.id,
                model_id: this.action.binding_model_id[0],
                res_ids: this.parent.props.activeIds,
                context: {
                    report_output_type: report_output_type,
                    report_repeat_count: has_repeat_count
                }
            }
        });
        let callback = _super.bind(this, this.action);
        this.preview_html(this.action, record_data.template, record_data.record, record_data.context, callback, report_output_type, has_repeat_count);
    },
    preview_html: function (action, mrt_data, record, context, callback, report_output_type, has_repeat_count) {
        var htmlPreview = new StimulsoftViewer(this, {
            action: action,
            mrt_data: mrt_data,
            record: record,
            context: context,
            callback: callback,
            report_output_type: report_output_type,
            has_repeat_count: has_repeat_count
        });
        htmlPreview.appendTo($('body'));
    }
});
