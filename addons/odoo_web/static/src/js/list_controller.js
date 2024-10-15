/** @odoo-module */

import ListController from 'web.ListController';
import view_registry from 'web.view_registry';
import DataExport from 'web.DataExport';
import { patch } from 'web.utils';

patch(ListController.prototype, 'ListController', {
    async on_attach_callback() {
        await this._super.apply(this, arguments);

        if (!this.$('.o_controller_with_side_panel').length
            && this.renderer.state.context
            && this.renderer.state.context.side_panel_res_id
            && this.renderer.state.context.side_panel_view
            && this.renderer.state.context.side_panel_model) {

            var viewID = await this._rpc({
                model: 'ir.ui.view',
                method: 'get_view_id',
                args: [this.renderer.state.context.side_panel_view],
            })
            var options = {
                modelName: this.renderer.state.context.side_panel_model,
                currentId: this.renderer.state.context.side_panel_res_id,
                withControlPanel: false,
                mode: 'readonly',
                isFromFormViewDialog: true
            }
            var FormView = view_registry.get('form');
            var viewInfo = await this.loadFieldView(this.renderer.state.context.side_panel_model, this.renderer.state.context, viewID, 'form');
            var controller = await new FormView(viewInfo, options).getController(this);
            var $content = this.$('.o_content');
            await controller.appendTo($content);

            this.$('.o_action.o_view_controller').addClass('o_controller_with_side_panel');
            var $sidePanel = this.$('.o_controller_with_side_panel');
            var $toggle = $('<i class="side_panel_switch fa fa-arrow-circle-right"/>');

            $content.append($toggle);
            $content.on('click', '.side_panel_switch',function () {
                $sidePanel.toggleClass('hide');
                $toggle.toggleClass('hide fa-arrow-circle-right fa-arrow-circle-left');
            });
            setTimeout($toggle.click.bind($toggle), 1000);
        }
    },
    _getExportDialogWidget() {
        let state = this.model.get(this.handle);
        let defaultExportFields = this.renderer.columns.filter(field => field.tag === 'field' && state.fields[field.attrs.name].exportable !== false).map(field => field.attrs.name);
        let groupedBy = this.renderer.state.groupedBy;
        return new DataExport(this, state, defaultExportFields, groupedBy,
            this.getDomain(), this.getSelectedIds());
    },
    getDomain() {
        let state = this.model.get(this.handle);
        let domain = this.isDomainSelected && state.getDomain();
        const selectedIds = this.getSelectedIds();
        if (!this.isDomainSelected && selectedIds && selectedIds.length) {
            if (domain === false) domain = [];
            domain.push(['id', 'in', selectedIds]);
        }
        return domain;
    },
    _onSelectionChanged: function (ev) {
        this._super.apply(this, arguments);
        this.$('.o_list_export_xlsx').toggle(true);
    },
})
