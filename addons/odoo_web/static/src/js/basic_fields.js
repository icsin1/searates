/** @odoo-module **/

import { FieldFloat, FieldMonetary, BooleanToggle } from "web.basic_fields";
import { patch } from 'web.utils';


patch(FieldFloat.prototype, 'FieldFloat', {
    _prepareInput: function ($input) {
        const res = this._super.apply(this, arguments);
        if (this.value === 0) {
            this.$input.val('');
            this.$input.attr('placeholder', this.nodeOptions.placeholder || "0.00" );
            return res;
        }
        return res
    },
    isValid: function () {
        const value = this.mode === "readonly" ? this.value : this.$input.val();
        if (this.record.evalModifiers(this.attrs.modifiers).required && value === '') {
            return false
        }
        return this._super.apply(this, arguments);
    },
});

patch(FieldMonetary.prototype, 'FieldMonetary', {
    _prepareInput: function ($input) {
        const res = this._super.apply(this, arguments);
        if (this.value === 0) {
            this.$input.val('');
            this.$input.attr('placeholder', this.nodeOptions.placeholder || "0.00" );
            return res;
        }
        return res
    },
    isValid: function () {
        const value = this.mode === "readonly" ? this.value : this.$input.val();
        if (this.record.evalModifiers(this.attrs.modifiers).required && value === '') {
            return false
        }
        return this._super.apply(this, arguments);
    },
});

patch(BooleanToggle.prototype, 'BooleanToggle', {
    //  If form view is in readonly mode then boolean_toggle will be disabled
    _onClick: async function (event) {
        event.stopPropagation();
        if (!this.$input.prop('disabled') && this.viewType === 'form' && this.mode === 'readonly') {
            return true;
        } else {
            return this._super.apply(this, arguments);
        }
    }
});
