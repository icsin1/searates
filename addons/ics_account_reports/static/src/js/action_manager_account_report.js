/** @odoo-module */

import { download } from "@web/core/network/download";
import { registry } from "@web/core/registry";

registry.category("action_handlers").add('ir_actions_account_report_download', async function executeAccountReportDownload({ env, action }) {
    env.services.ui.block();
    const url = "/download_content";
    const data = action.data;

    try {
        await download({ url, data });
    } finally {
        env.services.ui.unblock();
    }
});
