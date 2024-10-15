odoo.define('odoo_branding.model.Message', function (require) {
"use strict";

var Message = require('mail.model.Message');

Message.include({
    _getAuthorName: function () {
        if (this._isOdoobotAuthor()) {
            return "iONBot";
        }
        return this._super.apply(this, arguments);
    },
    getAvatarSource: function () {
        if (this._isOdoobotAuthor()) {
            return '/odoo_branding/static/images/systembot.png';
        }
        return this._super.apply(this, arguments);
    },
});

});    