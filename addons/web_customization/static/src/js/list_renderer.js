odoo.define('web_customization.ControlPanel', function (require) {
    "use strict";

const ControlPanel = require('web.ControlPanel');
const ListRenderer = require('web.ListRenderer');
const config = require('web.config');
const DataExport = require('web.DataExport');
const view_registry = require('web.view_registry');
const { patch } = require('web.utils');
var core = require('web.core');

const { Component } = owl;
const { xml } = owl.tags;
var QWeb = core.qweb;
var _t = core._t;

const DataFields = DataExport.extend({
    template: 'web.customization.FieldDialog',
    init: function (parent, record, defaultExportFields) {
        this._super.apply(this, arguments);
        this.parent = parent;
        this.title = _t('Field View')
        this.buttons = [
            {text: _t("Save"), click: this._onSaveFields, classes: 'btn-primary'},
            {text: _t("Reset"), click: this._onResetFields, classes: 'btn-danger'},
            {text: _t("Close"), close: true},
        ],
        this.records = {};
        this.record = record;
        this.defaultExportFields = defaultExportFields;
    },
    _showExportsList: function () {},
    _onShowData: function (records, expansion) {
        var self = this;
        this.$('.o_left_field_panel')
            .empty()
            .append($('<div/>')
            .addClass('o_field_tree_structure')
            .append(QWeb.render('web.customization.TreeItems', {fields: records.filter(e => !['id', '.id'].includes(e.id)), debug: config.isDebug()})) );

        _.extend(this.records, _.object(_.pluck(records, 'id'), records));
        this.$records = this.$('.o_export_tree_item');
        this.$records.each(function (i, el) {
            var $el = $(el);
            $el.find('.o_tree_column').first().toggleClass('o_required', !!self.records[$el.data('id')].required);
        });
    },
    _onSaveFields() {
        let viewFields = this.$('.o_export_field').map((i, field) => ({
                name: $(field).data('field_id'),
                index: i,
            }
        )).get();
        this._rpc({
            'model': 'base',
            'method': 'extend_view',
            'kwargs': {
                view_fields: viewFields,
                view_id: this.parent.controlPanelProps.view.view_id,
                original_view_id: this.parent.controlPanelProps.view.view_id,
                first_call: true,
            }
        }).then(window.location.reload.bind(window.location));
    },
    _onResetFields: function () {
        this._rpc({
            'model': 'base',
            'method': 'unlink_views',
            'args': [this.parent.controlPanelProps.view.view_id]
        }).then(window.location.reload.bind(window.location));
    }
})

class CustomFieldsView extends Component {
    onButtonClick() {
        let controller = this.__owl__.parent.__owl__.parent.parentWidget;
        let state = controller.model.get(controller.handle);
        let defaultExportFields = controller.renderer.columns.filter(field => field.tag === 'field' && state.fields[field.attrs.name].exportable !== false).map(field => field.attrs.name);
        new DataFields(controller, state, defaultExportFields).open();
    }
}
CustomFieldsView.template = xml`<div class="btn-group"><button t-on-click="onButtonClick" class="border btn btn-light fa fa-sliders"></button></div>`

patch (ControlPanel, 'web.customization.ControlPanel', {
    components: { ...ControlPanel.components, CustomFieldsView},
})

});
