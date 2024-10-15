
/** @odoo-module **/

import { patch } from 'web.utils';
import { NavBar } from "@web/webclient/navbar/navbar";

patch(NavBar.prototype, 'NavBar', {
    render: async function () {
        await this._super.apply(this, arguments);
        let activeMenu = this.getActiveMenu();
        this.setMenuActive(activeMenu);
    },
    getActiveMenu: function () {
        const queryParams = new URLSearchParams(window.location.href.split('#')[1]);
        const actionId = +queryParams.get('action');
        const allMenus = this.menuService.getAll();
        const menu = allMenus.find((m) => m.actionID === actionId);
        return menu || allMenus.length && allMenus[0]
    },
    onNavBarDropdownItemSelection: function (ev) {
        this._super.apply(this, arguments);
        const { payload: menu } = ev.detail;
        if (menu) {
            this.menuService.selectMenu(menu);
            this.setMenuActive(menu);

        }
    },
    setMenuActive: function (menu) {
        const allMenus = this.menuService.getAll();
        const parentMenu = allMenus.find((m) => m.children.includes(menu.id));
        let xmlid = parentMenu.xmlid;

        if (!parentMenu.xmlid && menu.children.length) {
            menu = allMenus.find((m) => m.id === menu.children[0]);
            xmlid = menu.xmlid
        }
        $(this.el).find(`.o_main_navbar .bg-200`).removeClass('bg-200');
        $(this.el).find(`a[data-section="${menu.id}"]`).addClass('bg-200');
        let $buttonMenu = $(this.el).find(`button[data-menu-xmlid="${xmlid}"]`);
        if (!$buttonMenu.length) {
            menu = allMenus.find((m) => m.children.includes(parentMenu.id));
            if (menu) {
                $buttonMenu = $(this.el).find(`button[data-menu-xmlid="${menu.xmlid}"]`);
            }
        }
        if ($buttonMenu.length) {
            $buttonMenu.addClass('bg-200')
        } else {
            const currentApp = this.menuService.getCurrentApp();
            if (currentApp && currentApp.children.length) {
                menu = allMenus.find((m) => m.id === currentApp.children[0]);
                $(this.el).find(`button[data-menu-xmlid="${menu.xmlid}"]`).addClass('bg-200')
            }
        }
    },
});
