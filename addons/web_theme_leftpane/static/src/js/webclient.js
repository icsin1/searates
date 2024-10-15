/** @odoo-module **/

import { WebClient } from "@web/webclient/webclient";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { useEffect } from "@web/core/utils/hooks";

const { useState } = owl;

export class MenuItemCustom extends DropdownItem {
    setup() {
        super.setup();
        useEffect(
            () => {
                if (this.state.payload.id) {
                    this.el.dataset.section = this.state.payload.id;
                }
                if (this.state.payload.xmlid) {
                    this.el.dataset.menuXmlid = this.state.payload.xmlid;
                }
            },
            () => []
        );
    }
    constructor(parent, props) {
        super(parent, props);
        this.parent = parent;
        this.state = useState({
            'parent': parent,
            'payload': this.getActiveMenu(),
        });
    }
    onClick(app, ev) {
        if (this.props.href){
            ev.preventDefault();
        }
        this.render();
        window.location.href = this.getMenuItemHref(app);

    }
    getMenuItemHref(payload) {
        const parts = [`menu_id=${payload.id}`];
        if (payload.actionID && !payload.appID) {
            parts.push(`action=${payload.actionID}`);
        }
        return "#" + parts.join("&");
    }
    getActiveMenu() {
        const queryParams = new URLSearchParams(window.location.href.split('#')[1]);
        const actionId = +queryParams.get('action');
        const allMenus = this.parent.menuService.getAll();
        const allApps = this.parent.menuService.getApps();
        const menu = allMenus.find((m) => m.actionID === actionId);
        return menu || allApps.length && allApps[0];
    }
    getActiveMenuByID() {
        const queryParams = new URLSearchParams(window.location.href.split('#')[1]);
        const menuID = +queryParams.get('menu_id');
        const allMenus = this.parent.menuService.getAll();
        const allApps = this.parent.menuService.getApps();
        const menu = allMenus.find((m) => m.id === menuID);
        return menu || allApps.length && allApps[0];
    }
    isActiveMenu(menu) {
        return this.getActiveMenuByID().id === menu.id
    }
}
MenuItemCustom.template = "web_theme_leftpane.MenuItem";
MenuItemCustom.props = undefined;
WebClient.components = {... WebClient.components, MenuItemCustom: MenuItemCustom}
