/** @odoo-module **/

import { symmetricalDifference } from "@web/core/utils/arrays";
import { companyService } from "@web/webclient/company_service";
import { patch } from 'web.utils';
import { browser } from "@web/core/browser/browser";

patch(companyService, 'customCompanyService', {
    start(env, { user, router, cookie }) {
        var res = this._super.apply(this, arguments);
        const allowedCompanyIds = res.allowedCompanyIds
        Object.assign(res, {
            async setCompanies(mode, ...companyIds) {
                // compute next company ids
                let nextCompanyIds;
                if (mode === "toggle") {
                    nextCompanyIds = symmetricalDifference(allowedCompanyIds, companyIds);
                } else if (mode === "loginto") {
                    const companyId = companyIds[0];
                    if (allowedCompanyIds.length === 1) {
                        // 1 enabled company: stay in single company mode
                        nextCompanyIds = [companyId];
                    } else {
                        // multi company mode
                        nextCompanyIds = [
                            companyId,
                            ...allowedCompanyIds.filter((id) => id !== companyId),
                        ];
                    }
                }
                nextCompanyIds = nextCompanyIds.length ? nextCompanyIds : [companyIds[0]];

                // apply them
                router.pushState({ cids: nextCompanyIds }, { lock: true });
                cookie.setCookie("cids", nextCompanyIds);
                const currentController = env.services.action.currentController;
                const view = currentController && currentController.views && currentController.views[0].type
                if(view){
                    await env.services.action.switchView(view)
                }
                browser.setTimeout(() => browser.location.reload()); // history.pushState is a little async
            },
        })
        return res
    }
});