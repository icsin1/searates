odoo.define('base_document_reports_stimulsoft.viewer', function (require) {
    "use strict";

var Widget = require('web.Widget');


var StimulsoftViewer = Widget.extend({
    template: "base_document_reports_stimulsoft.viewer",
    events: {
        'click .o_AttachmentViewer_buttonDownload': '_onDownload',
        'click .o_AttachmentViewer_headerItemButtonClose': '_onClose',
        'click .o_AttachmentViewer_buttonAction': '_onAction'
    },
    init: function (parent, options) {
        this._super.apply(this, arguments);
        this.options = options || {};
        this.parent = parent;
        this.context = this.options.context || {};
        this.buttons = parent.buttons || this.options.buttons || [];
        this.action = this.options.action;
        this.mrt_template = this.options.mrt_data;
        this.record = this.options.record;
        this.record_name = this.record.name || this.action.name;
        this.callback = this.options.callback;
        this.output_type = this.options.report_output_type;
        this.output_copies = this.options.has_repeat_count;
        this.report = this._generate_report();
        this._reset();
    },
    start: function () {
        this.$el.modal('show');
        this.$el.on('hidden.bs.modal', _.bind(this._onDestroy, this));

        const cssStyle = document.createElement("style");
        cssStyle.rel = "stylesheet";
        cssStyle.innerHTML = `button.download,button.openFile,a.bookmark { display: none !important; }`;

        var self = this;
        return this._super.apply(this, arguments).then(() => {
            self._render_html_preview();
        });
    },
    _generate_report: function () {
        // Setting License key
        if (this.context.gc_si_key) {
            Stimulsoft.Base.StiLicense.key = this.context.gc_si_key;
        }
        // Report
        var report = Stimulsoft.Report.StiReport.createNewReport();
        report.load(this.mrt_template);

        // Remove all connections from the report template
        report.dictionary.databases.clear();

        // Create new DataSet object
        var dataSet = new Stimulsoft.System.Data.DataSet("root");
        dataSet.readJson(this.record);

        // Register DataSet object
        report.regData("root", "root", dataSet);
        return report;
    },
    _get_options: function () {
        var options = new Stimulsoft.Viewer.StiViewerOptions();
        
        options.appearance.fullScreenMode = true;
        options.appearance.scrollbarsMode = true;
        options.appearance.showTooltips = false;
        options.appearance.backgroundColor = "";

        // Hide toolbar
        options.toolbar.visible = true;
        options.toolbar.showPrintButton = true;
        options.toolbar.showDesignButton = false;
        options.toolbar.showOpenButton = false;
        options.toolbar.showFullScreenButton = false;
        options.toolbar.showAboutButton = false;
        options.toolbar.showSaveButton = false;
        options.toolbar.viewMode = Stimulsoft.Viewer.StiWebViewMode.Continuous;
        options.toolbar.zoom = Stimulsoft.Viewer.StiZoomMode.PageWidth;
        options.toolbar.autoHide = true;
        return options;
    },

    _render_html_preview: function () {
        const report = this.report;
        var viewer = new Stimulsoft.Viewer.StiViewer(this._get_options(), "StiViewer", false);
        viewer.report = report;
        viewer.renderHtml(this.$('.o_AttachmentViewer_main')[0]);
    },
    _onClose: function (e) {
        e.preventDefault();
        this.destroy();
    },
    _onAction: async function(e) {
        const button = this.options.buttons.filter(button => button.string == e.currentTarget.querySelector('span').innerHTML);
        if (button.length) {
            button[0].callback(this);
        } else {
            let res = await this._rpc({
                model: this.parent.data.model,
                method: e.currentTarget.dataset.method,
                args: [this.parent.data.data.id],
            });
            if (res) {
                this.do_action(res);
            }
        }
        this.destroy();
    },
    destroy: function () {
        if (this.isDestroyed()) {
            return;
        }
        this.$el.modal('hide');
        this.$el.remove();
        this._super.apply(this, arguments);
    },
    _reset: function () {
        this.scale = 1;
        this.dragStartX = this.dragstopX = 0;
        this.dragStartY = this.dragstopY = 0;
    },
    _onClose: function (e) {
        e.preventDefault();
        this.destroy();
    },
    _onDestroy: function () {
        this.destroy();
    },
    _onDownload: function (e) {
        e.preventDefault();
        // EXPORT PDF
        var self = this;
        const report = this.report;
        const record_name = (this.record.name || '') + "_";
        report.renderAsync(function () {
            report.exportDocumentAsync(function (data) {
                Stimulsoft.System.StiObject.saveAs(data, self.action.name + '_' + record_name + "Report.pdf", "application/pdf");
            }, Stimulsoft.Report.StiExportFormat.Pdf);
        });
    },
});
return StimulsoftViewer;
});
