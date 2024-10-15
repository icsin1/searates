/** @odoo-module **/

import BasicController from 'web.BasicController';
import FormController from 'web.FormController';
import { patch } from 'web.utils';
import core from 'web.core';
import Dialog from 'web.Dialog';

var qweb = core.qweb;
var _t = core._t;

patch(BasicController.prototype, 'BasicController', {
    reload: function () {
        const prom = this._super.apply(this, arguments);
        const $content = this.$('.o_content');
        prom.finally($content.scrollTop.bind($content, $content.scrollTop()))
        return prom;
    },
    leavePageConfirmation: async function(){
        var self = this;
        return new Promise(function (resolve, reject) {
            var buttons = [{
                classes: 'btn-primary',
                click: () => {
                    resolve(true);
                },
                close: true,
                text: _t('Leave'),
            },
            {
                close: true,
                text: _t('Stay'),
                click: () => {
                    reject();
                },
            }];
            new Dialog(self, _.extend({
                size: 'medium',
                buttons: buttons,
                $content: $(qweb.render('leavePageConfirmation')),
                title: _t("Alert"),
            })).open({shouldFocusButtons:true});
       });
    },
    saveChanges: async function (recordId) {
        // waits for _applyChanges to finish
        await this.mutex.getUnlockedDef();
        recordId = recordId || this.handle;

        if (this.isDirty(recordId)) {
            if(this.mode == "edit"){
                await this.leavePageConfirmation();
                return Promise.resolve();
            }
            await this.savingDef;
            await this.saveRecord(recordId, {
                stayInEdit: true,
                reload: false,
            });
        }
    },
});

patch(FormController.prototype, 'FormController', {
    update: function () {
        const prom = this._super.apply(this, arguments);
        const $content = this.$('.o_content');
        prom.finally($content.scrollTop.bind($content, $content.scrollTop()))
        return prom;
    },
});
