odoo.define('odoo_branding.web.Dialog', function (require) {
"use strict";


var core = require('web.core');
var Dialog = require('web.Dialog');

var _t = core._t;

Dialog.include({
    init: function () {
        this._super.apply(this, arguments);
        if (_.str.contains(this.title, "Odoo")) {
            this.title = this.title.replace("Odoo", "System");
        }
    }
});

});