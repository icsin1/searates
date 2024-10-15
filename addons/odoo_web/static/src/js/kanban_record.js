odoo.define('odoo_web.kanban_record', function (require) {
"use strict";

var KanbanRecord = require('web.KanbanRecord');

KanbanRecord.include({
    _onKanbanActionClicked: function (event) {
        var $el = $(event.currentTarget);

        if ($el.attr('type') === 'move') {
            this.do_action($el.attr('action'), {
                additional_context: { default_active_id: this.id },
                on_close: (options) => {
                    if (!options || options && !options.special) {
                        this.trigger_up('reload', { keepChanges: true });
                    }
                },
            });
        } else {
            this._super.apply(this, arguments);
        }
    }
});
});
