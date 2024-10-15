/** @odoo-module alias=freight_management_charges.ShipmentChargeButtonsListView**/

import viewRegistry from "web.view_registry";
import ListView from "web.ListView";
import ListController from 'web.ListController';
var pyUtils = require('web.py_utils');


var ShipmentChargeListController = ListController.extend({
    buttons_template: 'ShipmentCharges.buttons',
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

var ShipmentChargeButtonsListView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Controller: ShipmentChargeListController,
    }),
});

viewRegistry.add('shipment_charge_additional_button', ShipmentChargeButtonsListView);

export default [ShipmentChargeListController, ShipmentChargeButtonsListView];
