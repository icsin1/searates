/** @odoo-module **/

import {download} from "@web/core/network/download";
import {registry} from "@web/core/registry";

registry
    .category("ir.actions.report handlers")
    .add("mrt_handler", async function (action, options, env) {
    if (action.report_type === 'mrt') {
        const type = action.report_type;
        const url = `report/${type}/${action.report_res_id}`;
        env.services.ui.block();
        try {
            await download({
                url: "/report/mrt/" + action.report_res_id,
                data: {
                    report_model: action.report_res_model,
                    report_res_id: action.report_res_id,
                    data: JSON.stringify([url, action.report_type, action.id]),
                    context: JSON.stringify({
                        ...env.services.user.context,
                        ...action.context
                    }),
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
        return true;
    }
});
