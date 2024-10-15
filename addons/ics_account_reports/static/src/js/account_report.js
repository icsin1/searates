/** @odoo-module **/

import AbstractAction from 'web.AbstractAction';
import BasicModel from 'web.BasicModel';
import { qweb as QWeb, _t } from 'web.core';
import Widget from 'web.Widget';
import StandaloneFieldManagerMixin from 'web.StandaloneFieldManagerMixin';
import datepicker from 'web.datepicker';
import field_utils from 'web.field_utils';
import { FieldMany2ManyTags } from 'web.relational_fields';
import { AccountReportSectionLine } from '@ics_account_reports/js/account_report_section_line';
var Dialog = require('web.Dialog');

var FieldM2M = Widget.extend(StandaloneFieldManagerMixin, {
    init: function (parent, field) {
        this._super.apply(this, arguments);
        StandaloneFieldManagerMixin.init.call(this);
        this.parent = parent;
        this.field = field;
        this.widget = false;
    },
    willStart: function () {
        return this._super.apply(this, arguments)
            .then(this._createWidget.bind(this, this.field))
    },
    start: function () {
        var $content = $(QWeb.render("ics_account_reports.widgetM2MList", {field: this.field}));
        this.$el.append($content);
        this.widget.appendTo($content.find('#'+this.field.fieldName+'_field'));
        return this._super.apply(this, arguments);
    },
    _confirmChange: function () {
        var result = StandaloneFieldManagerMixin._confirmChange.apply(this, arguments);
        var data = {};
        data[this.field.fieldName] = this.widget.value.res_ids;
        this.trigger_up('value_changed', data);
        this.parent.onFieldChance.call(this.parent, this, this.widget.value.res_ids);
        return result;
    },
    _createWidget: function (field) {
        var options = {};
        options[field.fieldName] = {
            options: { no_create_edit: true, no_create: true }
        };
        return this.model.makeRecord(field.modelName, [{
            fields: [{name: 'id', type: 'integer'}, {name: 'display_name', type: 'char'}],
            name: field.fieldName,
            relation: field.modelName,
            type: 'many2many',
            value: field.value,
            domain: field.domain,
        }], options).then((recordID)=> {
            this.widget = new FieldMany2ManyTags(this, field.fieldName, this.model.get(recordID), {mode: 'edit'} );
            this._registerWidget(recordID, field.fieldName, this.widget);
        });
    },
});

export const AccountingReportView = AbstractAction.extend({
    template: 'ics_account_reports.main_view',
    templateButtons: 'ics_account_reports.buttons',
    hasControlPanel: true,
    modelName: 'account.move.line',
    actionTitle: 'Account Report',
    events: {
        'click .ics_btn_refresh': '_onRefreshClick',
        'click .ics_expandable_row': '_onExpandableRowClick',
        'click .ics_journal_entries_row': '_onViewJournalEntriesRowClick',
        'click .ics_open_record': '_onOpenRecordClick',
        'click .sortable .ics_account_report_column_header.sortable': '_onHeaderClick'
    },
    config: _.extend({}, AbstractAction.prototype.config, {
        Model: BasicModel,
    }),
    report_kwargs: {},
    init: function (parent, action, options) {
        this._super.apply(this, arguments);

        this.action = action;
        this.context = action.context;
        this.report_kwargs['context'] = this.context;
        this.report_options = {};
        this.report_buttons = [];
        this.report_model = this.context.model;
        this.action_manager = parent;
        this.domain = [];
        this.options = options || {};
        this.searchModelConfig.modelName = this.modelName;
        this.controlPanelProps.cp_content = {};
        this.env = parent.env;
        this.widgets = [];
        this.__owl__ = {
            children: {},
        }
        this.model = new this.config.Model(this, {
            modelName: this.modelName,
        });
        this.report_data = {};
        this.FieldM2M = {};
    },
    willStart: async function () {
        return Promise.all([this._loadData(), this._super(...arguments)]);
    },
    start: function () {
        return this._super.apply(this, arguments)
            .then(this.update_cp.bind(this))
            .then(this.initComponents.bind(this));
    },
    reload: function() {
        _.each(this.widgets, (component)=> {
            component.destroy();
        });
        return this._loadData()
            .then(this.update_cp.bind(this))
            .then(this.initComponents.bind(this));
    },
    renderButtons: function() {
        var self = this;
        this.$buttons = $(QWeb.render("ics_account_reports.buttons", {report_buttons: this.report_buttons}));
        // bind actions
        _.each(this.$buttons.find('.ics_report_button'), function(el) {
            $(el).click(function() {
                self.$buttons.attr('disabled', true);
                return self._rpc({
                    model: self.report_model,
                    method: $(el).attr('action'),
                    args: [[self.context.id || false], self.report_options],
                    context: self.report_kwargs,
                })
                .then(function(result){
                    var doActionProm = self.do_action(result);
                    self.$buttons.attr('disabled', false);
                    return doActionProm;
                })
                .guardedCatch(function() {
                    self.$buttons.attr('disabled', false);
                });
            });
        });
        return this.$buttons;
    },
    renderSearchViewButtons: function () {
        var self = this;
        this.$searchview_buttons = $(QWeb.render("ics_account_reports.searchview_buttons", {
            options: this.report_options
        }));
        var $datePickers = this.$searchview_buttons.find('.js_account_reports_datetimepicker');
        var options = { locale : moment.locale(), format : 'L', icons: { date: "fa fa-calendar" } };

        $datePickers.each(function () {
            $(this).datetimepicker(options);
            var date = new datepicker.DateWidget(options);
            var name = $(this).find('input').attr('name');
            var value = $(this).data('default-value');

            date.replace($(this)).then(function () {
                date.$el.find('input').attr('name', name);
                if (value) {
                    date.setValue(moment(value));
                }
            });
        });
        _.each(this.$searchview_buttons.find('.js_format_date'), function(date) {
            var value = $(date).html();
            $(date).html((new moment(value)).format('ll'));
        });

        this.$searchview_buttons.find('.ics_ar_date_filter').removeClass('active');
        this.$searchview_buttons.find('.ics_ar_date_filter[data-filter=' + this.report_options.date.filter + ']').addClass('active');

        // date filter click events
        this.$searchview_buttons.find('.ics_ar_date_filter').click(function (event) {
            self.report_options.date.filter = $(this).data('filter');
            var error = false;
            if ($(this).data('filter') === 'custom') {
                var date_from = self.$searchview_buttons.find('.o_datepicker_input[name="date_from"]');
                var date_to = self.$searchview_buttons.find('.o_datepicker_input[name="date_to"]');
                if (date_from.length > 0){
                    error = date_from.val() === "" || date_to.val() === "";
                    self.report_options.date.date_from = field_utils.parse.date(date_from.val());
                    self.report_options.date.date_to = field_utils.parse.date(date_to.val());
                }
                else {
                    error = date_to.val() === "";
                    self.report_options.date.date_to = field_utils.parse.date(date_to.val());
                }
                if (date_to.val() && date_from.val() && field_utils.parse.date(date_to.val()) < field_utils.parse.date(date_from.val())){
                    Dialog.alert(this, _t('End date should be greater than the Start date.'));
                    return false;
                }
            }
            
            if (error) {
                Dialog.alert(self, _t("Date can't be empty."));
                return false;
            } else {
                self.reload();
            }
        });

        // Fold/Unfold
        this.$searchview_buttons.find('.ics_foldable_container').click(function (event) {
            event.stopPropagation();
            event.preventDefault();
            $(this).toggleClass('ics_closed_container ics_opened_container');
            self.$searchview_buttons.find('.ics_foldable_item[data-filter="'+$(this).data('filter')+'"]').toggleClass('ics_closed_container');
        });

        if (self.report_options.comparison) {
            // Marking component active
            this.$searchview_buttons.find('.js_account_report_date_cmp_filter').removeClass('active');
            this.$searchview_buttons.find('.js_account_report_date_cmp_filter[data-filter=' + self.report_options.comparison.filter + ']').addClass('active');

            // date filter click events
            this.$searchview_buttons.find('.js_account_report_date_cmp_filter').click(function (event) {
                self.report_options.comparison.filter = $(this).data('filter');
                var number_period = $(this).parent().find('input[name="periods_number"]');
                self.report_options.comparison.number_period = (number_period.length > 0) ? parseInt(number_period.val()) : 1;
                self.reload();
            });
        }

        // Tax Reports
        if (self.report_options.is_tax_report) {
            // Marking component active
            this.$searchview_buttons.find('.ics_ar_tax_report_filter').removeClass('active');
            this.$searchview_buttons.find('.ics_ar_tax_report_filter[data-filter=' + self.report_options.active_tax_report.id + ']').addClass('active');
            // tax_report filter click events
            this.$searchview_buttons.find('.ics_ar_tax_report_filter').click(function (event) {
                var tax_report_id = $(this).data('filter');
                var tax_report = self.report_options.tax_reports[tax_report_id];
                self.report_options.active_tax_report = tax_report;
                self.reload();
            });
        }
        for (let filter_key in this.report_options.filters) {
            let filter = this.report_options.filters[filter_key]
            if (!this.FieldM2M.hasOwnProperty(filter.res_field)) {
                this.FieldM2M[filter.res_field] = new FieldM2M(this, {
                    label: filter.string,
                    modelName: filter.res_model,
                    fieldName: filter.res_field,
                    value: filter.res_ids.map(Number),
                    domain: filter.domain,
                });
                this.FieldM2M[filter.res_field].appendTo(this.$searchview_buttons.find(`.js_field_m2m_${filter.res_field}`));
            } else {
                this.$searchview_buttons.find(` .js_field_m2m_${filter.res_field}`).append(this.FieldM2M[filter.res_field].$el);
            }
        }
    },
    onFieldChance: function (widget, res_ids) {
        this.report_options[widget.field.fieldName] = res_ids;
        this.reload();
    },
    // Updates the control panel and render the elements that have yet to be rendered
    update_cp: function() {
        this.renderButtons();
        this.renderSearchViewButtons();
        var status = {
            cp_content: {
                $buttons: this.$buttons,
                $searchview_buttons: this.$searchview_buttons,
            },
        };
        return this.updateControlPanel(status);
    },
    _loadData: function () {
        var self = this;
        return this._rpc({
            model: this.context.model,  // it contains report data model
            method: 'get_account_report_data',
            args: [[this.context.id || false], this.report_options],
            kwargs: this.report_kwargs
        }).then(function (result) {
            self.report_data = result;
            self.report_options = result.options;
            self.report_buttons = result.options.buttons;
            self.actionTitle = result.title;
        });
    },
    _updateControlPanel: function () {
        this.$buttons = $(QWeb.render(this.templateButtons, {widget: this}));
        for (let key in this.button_events) {
            let [ev, target] = key.split(' ');
            this.$buttons.on(ev, target, this[this.button_events[key]].bind(this));

        }
        var status = {
            title: this.actionTitle,
            cp_content: {$buttons: this.$buttons},
        };
        this.updateControlPanel(status);
    },
    _onRefreshClick: function () {
        this.reload()
    },
    _onHeaderClick: function (ev) {
        this.report_options.orderby = $(ev.currentTarget).text();
        this.report_options.reverse = !this.report_options.reverse;
        this.reload();
    },
    _findSection: function (children, key) {
        var section = children.find(s => s.id == key);
        if (!section && children.length > 0) {
            var parent_section = children.find(child => this._findSection(child.children, key));
            if (parent_section) {
                section = this._findSection(parent_section.children, key);
            }
        }
        return section;
    },
    _onExpandableRowClick: function (event) {
        event.stopPropagation();
        event.preventDefault();
        var self = this;
        var $el = $(event.currentTarget);
        const row_key = $el.data('key');
        const section = this._findSection(this.report_data.sections, row_key);

        $el.find('.fa').toggleClass('fa-caret-right fa-caret-down');
        if (section.is_expandable) {
            if ($el.hasClass('ics_section_expanded')) {
                $el.removeClass('ics_section_expanded');
            }
            self.$el.find("tr[data-parent-key='" + section.id + "']").toggleClass('d-none');
            return;
        }

        if ($el.hasClass('ics_section_expanded')) {
            $el.removeClass('ics_section_expanded');
            self.$el.find('.ics_child_group_lines_' + section.id).remove();
        } else {
            this._rpc({
                model: this.context.model,  // it contains report data model
                method: 'get_account_report_section_data',
                args: [[this.context.id || false], section, this.report_options],
                kwargs: this.report_kwargs
            }).then(function (lines) {
                $el.addClass('ics_section_expanded');
                if (lines.length > 0) {
                    var $dynamic_lines = $(QWeb.render("ics_account_reports.AccountReportSectionLineContainer", {
                        lines: lines, parent: section, headers: _.keys(section.values)
                    }));
                    $dynamic_lines.addClass('ics_child_group_lines_' + section.id);
                    $dynamic_lines.insertAfter($el);
                }
            });
        }
    },
    _onViewJournalEntriesRowClick: function (event) {
        event.stopPropagation();
        event.preventDefault();
        var self = this;
        var $el = $(event.currentTarget);
        return self._rpc({
            model: self.report_model,
            method: 'action_open_moves',
            args: [[self.context.id || false], $el.data('key'), self.report_options],
            context: self.report_kwargs,
        })
        .then(function(result) {
            self.do_action(result);
        });
    },
    _onOpenRecordClick: function (event) {
        event.stopPropagation();
        event.preventDefault();
        var self = this;
        var $el = $(event.currentTarget);
        return self._rpc({
            model: self.report_model,
            method: $el.data('method'),
            args: [[self.context.id || false], $el.data('record-id'), self.report_options],
            context: self.report_kwargs,
        })
        .then(function(result){
            var doActionProm = self.do_action(result);
            return doActionProm;
        });
    },
    initComponents: function () {
    }
});
