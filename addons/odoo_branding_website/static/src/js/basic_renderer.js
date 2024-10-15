odoo.define('odoo_branding.web.BasicRenderer', function (require) {
"use strict";

var BasicRenderer = require('web.BasicRenderer');

BasicRenderer.include({
    _renderNoContentHelper: function () {
        if (_.str.contains(this.noContentHelp, "Odoo")) {
            this.noContentHelp = this.noContentHelp.replace("Odoo", "System");
        }
        return this._super.apply(this, arguments);
    },
});

});    