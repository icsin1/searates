/** @odoo-module alias=odoo_web.field_web_preview**/

import field_registry from 'web.field_registry';
import { FieldMany2One } from 'web.relational_fields';
import PreviewWidget from 'odoo_web.preview';

var DocumentReportPreviewWidget = FieldMany2One.extend({
    init: function (parent, name, record, options) {
        this._super.apply(this, arguments);
        this.resID = this.record.data[this.attrs.options.res_id].res_id || this.record.data.id
        this.documentType = this.record.data[this.attrs.options.document_type]
    },
    start: async function () {
        return this._super.apply(this, arguments).then(async () => {
            if (this.documentType) {
                let render_data = await this._rpc({
                    model: this.documentType.model,
                    method: 'get_document_information',
                    args: [[this.documentType.res_id]]
                });

                let title = this.attrs.options.nolable ? '' : this.attrs.string ||this.field.string;
                return this._renderPreview(this.record, {
                    'resID': this.resID,
                    'name': this.record.data.name,
                    'type': render_data.output_type,
                    'render_action': render_data,
                    'attrs': {
                        'title': title,
                        'report_id': render_data.id,
                        'class': this.attrs.options.class
                    }
                }, render_data);
            }
        });
    },
    _renderPreview: function (record, render_attributes, render_data) {
        const preview = new PreviewWidget(this, record.data, render_attributes);
        return preview._widgetRenderAndInsert(() => {
            this.$el = preview.$el;
        });
    }
});

field_registry.add('web_preview', DocumentReportPreviewWidget);

export default {
    DocumentReportPreviewWidget: DocumentReportPreviewWidget
};
