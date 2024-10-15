/** @odoo-module **/

import FormController from 'web.FormController';
import FormView from 'web.FormView';
import viewRegistry from 'web.view_registry';

viewRegistry.add('colored_control_panel', FormView.extend({
    config: _.extend({}, FormView.prototype.config, {
        Controller: FormController.extend({
            start: async function () {
                const res = await this._super(...arguments);
                if (this.controlPanelProps.action.context.control_panel_class) {
                    this.$('.o_control_panel').addClass(this.controlPanelProps.action.context.control_panel_class);
                }
                return res;
            }
        }),
    }),
}));
