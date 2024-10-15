odoo.define('odoo_web.preview', function (require) {
'use strict';

var widgetRegistry = require('web.widget_registry');
var Widget = require('web.Widget');
var PDFViewer = require('odoo_web.pdf_viewer');

var PreviewWidget = Widget.extend({
    template: 'odoo_web.preview',
    init: function (parent, data, options) {
        this._super.apply(this, arguments);
        this.parent = parent;
        this.data = data;
        this.options = options;
        this.resID = options.resID || data.id;
        this.name = options.name || data.display_name;
        this.type = options.type;
        this.text = options.attrs.title || options.attrs.text;
        this.report = options.attrs.report;
        if (!this.report) {
            this.report_id = options.attrs.report_id;
        }
        this.method = options.attrs.method;
        this.class = options.attrs.class;
        this.render_action = options.render_action;
        this.action_string = options.attrs.action_string;
        this.buttons = options.attrs.buttons && JSON.parse(options.attrs.buttons.replaceAll("'", '"')) || [];
    },
    start: function () {
        return this._super.apply(this, arguments).then(() => {
            this.$el.on('click', this._onClickPreview.bind(this));
        });
    },
    preview_pdf: function (render_action, report_type, report_output_type, has_repeat_count) {
        var pdfviewer = new PDFViewer(this, {
            id: this.resID,
            report: render_action.id,
            name: render_action.name,
            report_res_model: render_action.report_res_model,
            report_res_id: render_action.report_res_id,
            type: 'binary',
            report_output_type: report_output_type,
            has_repeat_count: has_repeat_count,
            converter: report_type,
            mimetype: 'application/pdf',
        });
        pdfviewer.appendTo($('body'))
    },
    _onClickPreview: async function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        this.preview_pdf(this.render_action, this.type);
    },
});

widgetRegistry.add('web_preview', PreviewWidget);

return PreviewWidget;
});
