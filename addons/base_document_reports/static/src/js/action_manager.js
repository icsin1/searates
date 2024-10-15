/** @odoo-module **/

import {download} from "@web/core/network/download";
import {registry} from "@web/core/registry";

registry
    .category("ir.actions.report handlers")
    .add("docx_handler", async function (action, options, env) {
    if (action.report_type === 'docx'){
        const type = action.report_type;
        const url = `report/${type}/${action.context.active_ids.join(",")}`;
        env.services.ui.block();
        try {
            await download({
                url: "/report/docx/download",
                data: {
                    data: JSON.stringify([url, action.report_type, action.id]),
                    context: JSON.stringify(env.services.user.context),
                },
            });
        } finally {
            env.services.ui.unblock();
        }
        const onClose = options.onClose;
        if (action.close_on_report_download) {
            return doAction({ type: "ir.actions.act_window_close" }, { onClose });
        } else if (onClose) {
            onClose();
        }
    }
});
