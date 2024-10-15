/** @odoo-module **/

import { WebClient } from "@web/webclient/webclient";
import { patch } from 'web.utils';

patch(WebClient.prototype, 'WebClient', {
    setup() {
        this._super(...arguments);
        this.title.setParts({ zopenerp: "SearatesERP" });
    }

});
