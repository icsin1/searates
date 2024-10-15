odoo.define('odoo_web.datepicker', function (require) {
"use strict";

var DateWidget = require('web.datepicker').DateWidget;

DateWidget.include({
    init: function (parent, options) {
        if (options) {
            if (typeof options.minDate == 'string') {
                options.minDate = parent.record.data[options.minDate].format('YYYY/MM/DD')|| options.minDate
            }
            if (typeof options.maxDate == 'string') {
                options.maxDate = parent.record.data[options.maxDate].format('YYYY/MM/DD') || options.maxDate
            }
        }
        return this._super.apply(this, arguments);
    },

});

});
