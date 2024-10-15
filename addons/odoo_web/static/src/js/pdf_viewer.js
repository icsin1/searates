odoo.define('odoo_web.pdf_viewer', function (require) {
    "use strict";

var Widget = require('web.Widget');
var session = require ('web.session');

var PDFViewer = Widget.extend({
    template: "odoo_web.pdf_viewer",
    events: {
        'click .o_AttachmentViewer_buttonDownload': '_onDownload',
        'click .o_AttachmentViewer_headerItemButtonClose': '_onClose',
        'click .o_AttachmentViewer_buttonAction': '_onAction'
    },
    init: function (parent, attachment, options) {
        this._super.apply(this, arguments);
        this.options = options || {};
        this.parent = parent;
        this.activeAttachment = attachment;
        this.buttons = parent.buttons || this.options.buttons || [];
        this.modelName = 'ir.attachment';
        this.preview_url = this._generatePreviewURL();
        this._reset();
    },
    _generatePreviewURL: function () {
        var url = '/web/static/lib/pdfjs/web/viewer.html?'
        var report_model = this.activeAttachment.report_res_model || 'ir.actions.report';
        var document_path = '/report/' + this.activeAttachment.converter + '/' + this.activeAttachment.report + "/" + this.activeAttachment.id + "/" + report_model + "/{}?"
        if (this.activeAttachment.report_output_type) {
            document_path = document_path + "report_output_type=" + (this.activeAttachment.report_output_type || 'pdf') + "&";
        }
        if (this.activeAttachment.has_repeat_count) {
            document_path = document_path + "has_repeat_count=" + this.activeAttachment.has_repeat_count 
        }
        return url + "file=" + encodeURIComponent(document_path);
    },
    start: function () {
        this.$el.modal('show');
        this.$el.on('hidden.bs.modal', _.bind(this._onDestroy, this));

        const cssStyle = document.createElement("style");
        cssStyle.rel = "stylesheet";
        cssStyle.innerHTML = `button.download,button.openFile,a.bookmark { display: none !important; }`;

        return this._super.apply(this, arguments).then(() => {
            const iframe = this.el.querySelector('iframe');
            iframe.addEventListener('load', event => {
                if (iframe.contentDocument && iframe.contentDocument.head) {
                    iframe.contentDocument.head.appendChild(cssStyle);
                }
            });
        });
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
        $('#download', this.$('iframe').contents()).click();
    },
});
return PDFViewer;
});
