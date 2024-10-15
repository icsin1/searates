odoo.define('odoo_web.action_report_viewer', function (require) {
    "use strict";

var PDFViewer = require('odoo_web.pdf_viewer');
var Widget = require('web.Widget');

var ActionReportViewer = Widget.extend({
    init: function (parent, action, render_action, report_type, options) {
        this._super.apply(this, arguments);
        this.options = options || {};
        this.action = action;
        this.parent = parent;
        this.render_action = render_action;
        this.report_type = report_type;
    },
    view_report: function (report_output_type, has_repeat_count) {
        var pdfviewer = new PDFViewer(this, {
            id: this.parent.props.activeIds[0],
            report: this.render_action.id,
            name: this.render_action.name,
            report_res_model: this.render_action.report_res_model,
            report_res_id: this.render_action.report_res_id,
            type: 'binary',
            report_output_type: report_output_type,
            has_repeat_count: has_repeat_count,
            converter: this.report_type,
            mimetype: 'application/pdf',
        });
        pdfviewer.appendTo($('body'))
    }
});
return ActionReportViewer;
});
