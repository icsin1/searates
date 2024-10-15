/** @odoo-module **/

import dialogs from "web.view_dialogs";
import core from "web.core";
import { patch } from 'web.utils';
import ActionReportViewer from 'odoo_web.action_report_viewer';

var _t = core._t;

patch(ActionReportViewer.prototype, 'DocumentsActionReportViewer', {
    view_report: function (report_output_type, has_repeat_count) {
        var self = this;
        let _super = this._super;
        if (this.render_action.show_wizard) {
            let report_output_type = false;
            let has_repeat_count = 0;
            this.parent.rpc({
                model: 'ir.ui.view',
                method: 'get_view_id',
                args: ['base_document_reports.report_type_view_form'],
            }).then((ids) => {
                var context = this.parent.props.context || {};
                context.res_id = this.parent.props.activeIds && this.parent.props.activeIds[0];
                context.res_model = this.parent.env.action.res_model;
                new dialogs.FormViewDialog(this.parent.__owl__.parent.__owl__.parent.parentWidget, {
                    res_model: "report.type",
                    view_id: ids,
                    title: _t("Report Type"),
                    save_text: _t('Preview'),
                    context: context,
                    disable_multiple_selection: true,
                    on_saved: (record) => {
                        report_output_type = record.data.report_type_id.data.display_name
                        has_repeat_count = record.data.has_repeat_count
                        return _super.apply(self, [report_output_type, has_repeat_count]);
                    },
                }).open();
            });
        } else {
            return _super.apply(this, arguments);
        }
    }
});
