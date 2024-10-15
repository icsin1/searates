odoo.define('odoo_web.AppSwitcher', function(require) {
"use strict";
var AppsMenu = require("web.AppsMenu");
var ActionManager = require("web.ActionManager");
var core = require("web.core");
var config = require("web.config");
var QWeb = core.qweb;

function findNames(memo, menu) {
    if (menu.action) {
        var key = menu.parent_id ? menu.parent_id[1] + "/" : "";
        memo[key + menu.name] = menu;
    }
    if (menu.children.length) {
        _.reduce(menu.children, findNames, memo);
    }
    return memo;
}
/* Hide AppDrawer in desktop and mobile modes.
    * To avoid delays in pages with a lot of DOM nodes we make
    * sub-groups' with 'querySelector' to improve the performance.
    */
function closeAppDrawer() {
    _.defer(function() {
        // Need close AppDrawer?
        var menu_apps_dropdown = document.querySelector(".o_menu_apps .dropdown");
        $(menu_apps_dropdown)
            .has(".dropdown-menu.show")
            .find("> a")
            .dropdown("toggle");
        // Need close Sections Menu?
        // TODO: Change to 'hide' in modern Bootstrap >4.1
        var menu_sections = document.querySelector(
            ".o_menu_sections li.show .dropdown-toggle"
        );
        $(menu_sections).dropdown("toggle");
        // Need close Mobile?
        var menu_sections_mobile = document.querySelector(".o_menu_sections.show");
        $(menu_sections_mobile).collapse("hide");
    });
}

// Hide AppDrawer or Menu when the action has been completed
ActionManager.include({
    /**
     * @override
     */
    _appendController: function() {
        this._super.apply(this, arguments);
        closeAppDrawer();
    },
});

AppsMenu.include({
    events: _.extend(
        {
            "keydown .search-input input": "_searchResultsNavigate",
            "input .search-input input": "_searchMenusSchedule",
            "click .o-menu-search-result": "_searchResultChosen",
            "shown.bs.dropdown": "_searchFocus",
            "hidden.bs.dropdown": "_searchReset",
            "hide.bs.dropdown": "_hideAppsMenu",
        },
        AppsMenu.prototype.events
    ),
    init: function(parent, menuData) {
        this._super.apply(this, arguments);
        // Keep base64 icon for main menus
        for (const n in this._apps) {
            this._apps[n].web_icon_data = menuData.children[n].web_icon_data;
        }
        this._searchableMenus = _.reduce(menuData.children, findNames, {});
        this._search_def = false;
    },
    start: function() {
        this.$search_container = this.$(".search-container");
        this.$search_input = this.$(".search-input input");
        this.$search_results = this.$(".search-results");
        return this._super.apply(this, arguments);
    },
    /**
     * Prevent the menu from being opened twice
     *
     * @override
     */
    _onAppsMenuItemClicked: function(ev) {
        this._super.apply(this, arguments);
        ev.preventDefault();
        ev.stopPropagation();
    },
    /**
     * Get all info for a given menu.
     *
     * @param {String} key
     * Full path to requested menu.
     *
     * @returns {Object}
     * Menu definition, plus extra needed keys.
     */
    _menuInfo: function(key) {
        const original = this._searchableMenus[key];
        return _.extend({
                action_id: parseInt(original.action.split(",")[1], 10),
            }, original
        );
    },
    /**
     * Autofocus on search field on big screens.
     */
    _searchFocus: function() {
        if (!config.device.isMobile) {
            // This timeout is necessary since the menu has a 100ms fading animation
            setTimeout(() => this.$search_input.focus(), 100);
        }
    },

    /**
     * Reset search input and results
     */
    _searchReset: function() {
        this.$search_container.removeClass("has-results");
        this.$search_results.empty();
        this.$search_input.val("");
    },

    /**
     * Schedule a search on current menu items.
     */
    _searchMenusSchedule: function() {
        this._search_def = new Promise(resolve => {
            setTimeout(resolve, 50);
        });
        this._search_def.then(this._searchMenus.bind(this));
    },

    /**
     * Search among available menu items, and render that search.
     */
    _searchMenus: function() {
        const query = this.$search_input.val();
        if (query === "") {
            this.$search_container.removeClass("has-results");
            this.$search_results.empty();
            return;
        }
        var results = fuzzy.filter(query, _.keys(this._searchableMenus), {
            pre: "<b>",
            post: "</b>",
        });
        this.$search_container.toggleClass("has-results", Boolean(results.length));
        this.$search_results.html(
            QWeb.render("odoo_web.MenuSearchResults", {
                results: results,
                widget: this,
            })
        );
    },

    /**
     * Use chooses a search result, so we navigate to that menu
     *
     * @param {jQuery.Event} event
     */
    _searchResultChosen: function(event) {
        event.preventDefault();
        event.stopPropagation();
        const $result = $(event.currentTarget),
            text = $result.text().trim(),
            data = $result.data(),
            suffix = ~text.indexOf("/") ? "/" : "";
        // Load the menu view
        this.trigger_up("menu_clicked", {
            action_id: data.actionId,
            id: data.menuId,
            previous_menu_id: data.parentId,
        });
        // Find app that owns the chosen menu
        const app = _.find(this._apps, function(_app) {
            return text.indexOf(_app.name + suffix) === 0;
        });
        // Update navbar menus
        core.bus.trigger("change_menu_section", app.menuID);
    },

    /**
     * Navigate among search results
     *
     * @param {jQuery.Event} event
     */
    _searchResultsNavigate: function(event) {
        // Find current results and active element (1st by default)
        const all = this.$search_results.find(".o-menu-search-result"),
            pre_focused = all.filter(".active") || $(all[0]);
        let offset = all.index(pre_focused),
            key = event.key;
        // Keyboard navigation only supports search results
        if (!all.length) {
            return;
        }
        // Transform tab presses in arrow presses
        if (key === "Tab") {
            event.preventDefault();
            key = event.shiftKey ? "ArrowUp" : "ArrowDown";
        }
        switch (key) {
            // Pressing enter is the same as clicking on the active element
            case "Enter":
                pre_focused.click();
                break;
            // Navigate up or down
            case "ArrowUp":
                offset--;
                break;
            case "ArrowDown":
                offset++;
                break;
            default:
                // Other keys are useless in this event
                return;
        }
        // Allow looping on results
        if (offset < 0) {
            offset = all.length + offset;
        } else if (offset >= all.length) {
            offset -= all.length;
        }
        // Switch active element
        const new_focused = $(all[offset]);
        pre_focused.removeClass("active");
        new_focused.addClass("active");
        this.$search_results.scrollTo(new_focused, {
            offset: {
                top: this.$search_results.height() * -0.5,
            },
        });
    },
    /*
    * Control if AppDrawer can be closed
    */
    _hideAppsMenu: function() {
        return !this.$("input").is(":focus");
    },
});

});
