/** @odoo-module alias=fm_service_job_charge.ServiceJobChargeButtonsListView**/

import viewRegistry from "web.view_registry";
import ListView from "web.ListView";
import ListController from 'web.ListController';
var pyUtils = require('web.py_utils');


var ServiceJobChargeListController = ListController.extend({
    buttons_template: 'ServiceJobCharges.buttons',
    events: _.extend({}, ListController.prototype.events, {
        'click .ics_charge_button': '_onChargeButtonClick',
    }),
    _onChargeButtonClick: function (ev) {
        ev.preventDefault();
        var $el = $(ev.currentTarget);
        var context = pyUtils.eval('context', $el.data('pycontext'), this.controlPanelProps.action.context);
        var action = $el.data('action');
        if (action) {
            return this._doAction(action, context);
        }
    },
    _doAction: function (action, context) {
        var self = this;
        var params = {
            model: this.modelName,
            method: action,
            args: [this.controlPanelProps.action.context.active_id],
            context: context
        }
        return this._rpc(params).then(function(action) {
            if (action){
                self.do_action(action, {on_close: self.reload.bind(this, {})});
            }
            else{
                self.reload();
            }
        });
    }
    
});

var ServiceJobChargeButtonsListView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Controller: ServiceJobChargeListController,
    }),
});

viewRegistry.add('service_job_charge_additional_button', ServiceJobChargeButtonsListView);

export default [ServiceJobChargeListController, ServiceJobChargeButtonsListView];
