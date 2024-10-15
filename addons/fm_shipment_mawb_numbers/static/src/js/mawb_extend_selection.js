/** @odoo-module **/

import viewRegistry from "web.view_registry";
import ListView from "web.ListView";
import ListController from 'web.ListController';
import core from 'web.core';
import config from 'web.config';

var qweb = core.qweb;

var MAWBExtendSelectionController = ListController.extend({
    init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);
        this.customSelectionLength = 0;
        this.customSelection = false;
    },
    renderButtons: function ($node) {
        this._super.apply(this, arguments);
        var $input = $('<input />', {
            'type': 'number',
            'class': 'mx-2 o_list_mawb_extend_selection_input',
            'style': 'width: 150px;',
            'placeholder': 'Input Number To Select',
            'title': 'Input number and hit enter to select records',
            'min': 0,
        })
        $input.on('change', this._onExtendedSelectionKeyDown.bind(this))
        if ($node) {
            $input.appendTo($node.find('div'));
        }
    },
    updateButtons: function (mode) {
        this._super.apply(this, arguments)
        this.$el.find('.o_list_mawb_extend_selection_input').val(0)
    },
    _onExtendedSelectionKeyDown: async function(ev){
        ev.preventDefault();
        var self = this;
        var target = $(ev.currentTarget);
        const value = parseInt($(target).val());
        if(value < 0){
            this.displayNotification({ message: "Value must not be negative", type: 'danger' });
            $(target).addClass('border')
            $(target).addClass('border-danger')
            return
        }
        const state = this.model.get(this.handle);
        if(state.groupedBy.length && !state.res_ids.length){
            return
        }

        var $checkbox_input = self.renderer._getSelectableRecordCheckboxes()
        $checkbox_input.prop('checked', false);
        if($checkbox_input.length > value){
            $checkbox_input = $checkbox_input.slice(0, value)
        }
        $checkbox_input.each(function (index, input) {
            $(input).prop('checked', true)
        });
        this.renderer._updateSelection()
        const selected_ids = _.map(state.data.slice(0, value), function(rec){
            return rec.id
        });
        this.selection = selected_ids;
        var customSelectionLength = parseInt(value);
        if(state.groupedBy.length && state.res_ids.length < customSelectionLength){
            customSelectionLength = state.res_ids.length
        } else if(state.count < customSelectionLength){
            customSelectionLength = state.count
        }
        this.customSelectionLength = customSelectionLength;
        this.customSelection = true;
        this.renderer.trigger_up('selection_changed', { selection: this.selection });
        this.renderer._updateFooter();
        this._updateSelectionBox()
    },
    getSelectedIdsWithDomain: async function () {
        if (this.isDomainSelected) {
            const state = this.model.get(this.handle, {raw: true});
            return await this._domainToResIds(state.getDomain(), session.active_ids_limit);
        } else if(this.customSelection){
            const state = this.model.get(this.handle, {raw: true});
            return await this._domainToResIds(state.getDomain(), this.customSelectionLength);
        } else {
            return Promise.resolve(this.model.localIdsToResIds(this.selectedRecords));
        }
    },
    _updateSelectionBox() {
        this._renderHeaderButtons();
        if (this.$selectionBox) {
            this.$selectionBox.remove();
            this.$selectionBox = null;
        }
        if (this.selectedRecords.length) {
            const state = this.model.get(this.handle, {raw: true});
            this.$selectionBox = $(qweb.render('ListView.selection', {
                isDomainSelected: this.isDomainSelected,
                isMobile: config.device.isMobile,
                isPageSelected: this.isPageSelected,
                nbSelected: this.customSelectionLength || this.selectedRecords.length,
                nbTotal: state.count,
            }));
            this.$selectionBox.appendTo(this.$buttons);
        }
    },
});

var MAWBExtendSelection = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Controller: MAWBExtendSelectionController,
    }),
});

viewRegistry.add('mawb_extend_selection', MAWBExtendSelection);
