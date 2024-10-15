/** @odoo-module **/

import viewRegistry from "web.view_registry";
import FormView from "web.FormView";
import FormController from 'web.FormController';
import Dialog from 'web.Dialog';
import core from 'web.core';
const _t = core._t;

var PartnerFormController = FormController.extend({
    _validatePartner: function () {
        var self = this;
        var def = new Promise(function (resolve, reject) {
            var message = _t("Record(s) with the same name and email address already exist. Are you sure you want to save this record?");
            var dialog = Dialog.confirm(self, message, {
                title: _t("Warning"),
                confirm_callback: resolve,
                cancel_callback: reject,
            });
        });
        return def;
    },
    check_duplicate: async function(){
        await this.update({}, {reload: false});
        var data = this.renderer.state.data;
        return this._rpc({
            model: 'res.partner',
            method: 'check_duplicate',
            args: [data.id, data.name, data.email],
        });
    },
    saveRecord: async function () {
        var _super = this._super.bind(this);
        var is_duplicate_record = await this.check_duplicate()
        if(is_duplicate_record){
            return this._validatePartner().then(() => _super());
        } else {
            return _super();
        }
    },
});

var PartnerFormView = FormView.extend({
    config: _.extend({}, FormView.prototype.config, {
        Controller: PartnerFormController,
    }),
});

viewRegistry.add('partner_form', PartnerFormView);
