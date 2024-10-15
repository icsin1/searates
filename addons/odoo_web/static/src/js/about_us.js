/** @odoo-module **/

import { registry } from "@web/core/registry";

const serviceRegistry = registry.category("services");
const userMenuRegistry = registry.category("user_menuitems");

var core = require('web.core');
var rpc = require('web.rpc');
var QWeb = core.qweb;

function about_us_dialog(env) {
    return {
        type: "item",
        id: "about_us",
        description: env._t("About"),
        callback: () => {
            rpc.query({
                route: '/app/version_info',
            }).then((info) =>{
                if (!$('body').find('#aboutDetails').length) {
                   $('body').append(QWeb.render('about_details_dialog', {info: info}));
                }
                $('#aboutDetails').modal('show');
            });
        },
        sequence: 60,
    };
}

const BaseSetupMenuService = {
    start() {
        userMenuRegistry.add("about_us", about_us_dialog);
    },
};
serviceRegistry.add("BaseSetupMenuService", BaseSetupMenuService);
