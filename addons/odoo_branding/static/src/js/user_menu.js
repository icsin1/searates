/** @odoo-module **/

import { registry } from "@web/core/registry";

const serviceRegistry = registry.category("services");
const userMenuRegistry = registry.category("user_menuitems");

const customMenuService = {
    start() {
        userMenuRegistry.remove('documentation');
        userMenuRegistry.remove('support');
        userMenuRegistry.remove('odoo_account');
    },
};
serviceRegistry.add("customMenuService", customMenuService);
