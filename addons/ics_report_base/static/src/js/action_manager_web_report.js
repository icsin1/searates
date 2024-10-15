/** @odoo-module */

import { download } from "@web/core/network/download";
import { registry } from "@web/core/registry";

registry.category("action_handlers").add('ir_actions_web_report_download', async function executeWebReportDownload({ env, action }) {
    env.services.ui.block();
    const url = "/web/report/download";
    const data = action.data;

    try {
        await download({ url, data });
    } finally {
        env.services.ui.unblock();
    }
});
