/** @odoo-module **/

import ActionMenus from "web.ActionMenus";
import { patch } from 'web.utils';
import session  from 'web.session';
import ActionReportViewer from 'odoo_web.action_report_viewer';
const Context = require('web.Context');


patch(ActionMenus.prototype, 'ActionMenus', {
    async _executeAction(action) {
        let _super = this._super;
        if (this.env.view.type != 'form' || this.printItems.filter(e => e.action.id == action.id).length <= 0) {
            return _super.apply(this, arguments);
        }

        let activeIds = this.props.activeIds;
        if (this.props.isDomainSelected) {
            activeIds = await this.rpc({
                model: this.env.action.res_model,
                method: 'search',
                args: [this.props.domain],
                kwargs: {
                    limit: this.env.session.active_ids_limit,
                    context: this.props.context,
                },
            });
        }
        const activeIdsContext = {
            active_id: activeIds[0],
            active_ids: activeIds,
            active_model: this.env.action.res_model,
        };
        const context = new Context(this.props.context, activeIdsContext).eval();

        const load_action = await this.rpc({
            route: '/web/action/load',
            params: {
                action_id: action.id,
                additional_context: context,
            },
        });
        let render_action = false;
        let report_type = load_action.report_type;
        if (load_action.report_type != 'qweb-pdf') {
            [render_action] = await this.rpc({
                model: load_action.report_res_model,
                method: 'search_read',
                domain: [['report_id', '=', action.id]],
                fields: ['id', 'name', 'show_wizard', 'output_type'],
                limit: 1
            });
            render_action['report_res_model'] = load_action.report_res_model
            render_action['report_res_id'] = load_action.report_res_id
        } else {
            render_action = {
                'id': load_action.id,
                'filename': load_action.name,
                'report_res_model': false,
                'report_res_id': false
            }
            report_type = 'pdf';
        }
        var action_report_viewer = new ActionReportViewer(this, load_action, render_action, report_type, {context: context});
        action_report_viewer.view_report();
    },
});
