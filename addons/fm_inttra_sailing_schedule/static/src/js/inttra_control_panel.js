/** @odoo-module **/

import viewRegistry from "web.view_registry";
import ListView from "web.ListView";
import ListController from 'web.ListController';

var INTTRAScheduleServicePanel = ListController.extend({
    buttons_template: 'FreightINTTRAControlPanel.ServiceButtons',
    renderButtons: function () {
        var self = this;
        this._super.apply(this, arguments);
        let context = this.controlPanelProps.action.context;
        context['default_source'] = 'inttra';

        this.$buttons.on('click', '.o_button_fetch_inttra_schedule', function () {
            return self._rpc({
                model: 'freight.schedule',
                method: 'action_inttra_search_wizard',
                args: [],
                context: context,
            }).then(function(result) {
                self.do_action(result, {on_close: self.reload.bind(this, {})});
            });
        });
    },
});

var INTTRAServiceListView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Controller: INTTRAScheduleServicePanel,
    }),
});

viewRegistry.add('fm_inttra_sailing_schedule.fetch_schedules', INTTRAServiceListView);
