/** @odoo-module **/

import viewRegistry from "web.view_registry";
import ListView from "web.ListView";
import ListController from 'web.ListController';

var OAGScheduleServicePanel = ListController.extend({
    buttons_template: 'FreightOAGControlPanel.ServiceButtons',
    renderButtons: function () {
        var self = this;
        this._super.apply(this, arguments);
        let context = this.controlPanelProps.action.context;
        context['default_source'] = 'oag';

        this.$buttons.on('click', '.o_button_fetch_oag_schedule', function () {
            return self._rpc({
                model: 'freight.air.schedule',
                method: 'action_oag_search_wizard',
                args: [],
                context: context,
            }).then(function(result) {
                self.do_action(result, {on_close: self.reload.bind(this, {})});
            });
        });
    },
});

var OAGServiceListView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Controller: OAGScheduleServicePanel,
    }),
});

viewRegistry.add('fm_oag_air_schedule.fetch_schedules', OAGServiceListView);
