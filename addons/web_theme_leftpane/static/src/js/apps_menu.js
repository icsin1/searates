odoo.define('web_theme_leftpane.AppsMenu', function (require) {
"use strict";

var config = require('web.config');
var AppsMenu = require('web.AppsMenu');

AppsMenu.include({
    template: "WebThemeLeftPane.AppsMenu",
    init: function (parent, menuData) {
        this._super.apply(this, arguments);
        this._debugMode = config.isDebug();
        var session = this.getSession();
        this.user_name = session.name;
        this.user_avatar = session.url('/web/image', {
            model:'res.users',
            field: 'image_128',
            id: session.uid,
        });
        // Keep base64 icon for main menus
        for (const n in this._apps) {
            var theme_icon = menuData.children[n].theme_menu_icon;
            var web_icon = menuData.children[n].web_icon_data;
            this._apps[n].web_icon_data = theme_icon ? theme_icon : web_icon;
        }
    },
    _onAppsMenuItemClicked: function (ev) {
        ev.preventDefault();
        this._super.apply(this, arguments);
    }
});

});
