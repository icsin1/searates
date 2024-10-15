odoo.define('odoo_branding.UserMenu', function (require) {
"use strict";

var UserMenu = require('web.UserMenu');

UserMenu.include({
    _onMenuDocumentation: function () {
        window.open(window.location.protocol + "//" + window.location.hostname + "/doc")
    }
});

});    