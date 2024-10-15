/** @odoo-module */

import ListRenderer from 'web.ListRenderer';
import KanbanRecord from 'web.KanbanRecord';
import { patch } from 'web.utils';

patch(ListRenderer.prototype, 'ics_web_record_view.ListRenderer', {
    events: _.extend({}, ListRenderer.prototype.events, {
        'dblclick tbody tr': '_onRowDoubleClicked',
    }),
    async _onRowDoubleClicked(ev) {
        if (!ev.target.closest('.o_list_record_selector') && !$(ev.target).prop('special_click') && !this.arch.attrs.editable) {
            var id = $(ev.currentTarget).data('id');
            if (id) {
                this.trigger_up('open_record', { id: id, target: ev.target });
            }
        }
    },
    async _onRowClicked(ev){
        if (this.getParent().viewType != 'list') {
            await this._super.apply(this, arguments);
        }
    }
})

patch(KanbanRecord.prototype, 'ics_web_record_view.KanbanRecord', {
    _render: function () {
        return this._super.apply(this, arguments).then(() => {
            if (this.$el.hasClass('oe_kanban_global_click') ||
                this.$el.hasClass('oe_kanban_global_click_edit')) {
                if (this.getParent().getParent().viewType == 'kanban') {
                    this.$el.off('click');
                    this.$el.on('dblclick', this._onGlobalClick.bind(this));
                }
            }
        });
    },
})
