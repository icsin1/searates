odoo.define('odoo_web.fold_blank_kanban_stage_view', function (require) {
    'use strict';

    var KanbanRenderer = require('web.KanbanRenderer');

    KanbanRenderer.include({
        _renderView: function () {
            return this._super.apply(this, arguments).then(() => {
                this.widgets.forEach(widget => {
                    if (widget.data && (!widget.data.data.length && !widget.$el.hasClass('o_column_folded') ||
                        (widget.data.count > 0 && widget.$el.hasClass('o_column_folded')))) {
                        widget.trigger_up('column_toggle_fold');
                    }
                });
            })
        },
    });
});
