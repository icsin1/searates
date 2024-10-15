/** @odoo-module **/

import AbstractField from 'web.AbstractField';
import fieldRegistry from 'web.field_registry';


fieldRegistry.add("do_action", AbstractField.extend({
    events: _.extend({}, AbstractField.prototype.events, {
        'click .do_action': '_onDoAction',
    }),
    _renderReadonly: function () {
        this._super.apply(this, arguments);
        this.$el.html(`<span class="do_action badge badge-pill ${this.attrs.options.class || 'badge-primary'}">${this._formatValue(this.value)}</span>`);
    },
    _onDoAction: function (ev){
        ev.preventDefault();
        ev.stopPropagation();

        this.do_action(this.attrs.options.action, {
            additional_context: {
                active_id: this.record.data.id,
                create: 0,
                delete: 0
            },
        });
    }
}));
