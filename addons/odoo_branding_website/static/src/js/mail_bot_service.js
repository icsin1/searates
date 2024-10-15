odoo.define('odoo_branding.mail_bot.MailBotService', function (require) {
"use strict";

var core = require('web.core');
var MailBotService = require('mail_bot.MailBotService');

var _t = core._t;

MailBotService.include({
    getPreviews: function (filter) {
        if (!this.isRequestingForNativeNotifications()) {
            return [];
        }
        if (filter && filter !== 'mailbox_inbox') {
            return [];
        }
        var previews = [{
            title: _t("iONBot has a request"),
            imageSRC: "/odoo_branding/static/images/systembot.png",
            status: 'bot',
            body:  _t("Enable desktop notifications to chat"),
            id: 'request_notification',
            unreadCounter: 1,
        }];
        return previews;
    },
});

});    