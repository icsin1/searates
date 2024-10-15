/** @odoo-module **/

import AbstractAction from 'web.AbstractAction';
import BasicModel from 'web.BasicModel';
import { qweb as QWeb, _t } from 'web.core';
import Widget from 'web.Widget';
import StandaloneFieldManagerMixin from 'web.StandaloneFieldManagerMixin';
import datepicker from 'web.datepicker';
import field_utils from 'web.field_utils';
import { FieldMany2One, FieldMany2ManyTags } from 'web.relational_fields';
// import { WebReportSectionLine } from '@ics_report_base/js/web_report_section_line';
var Dialog = require('web.Dialog');

var FieldM2x = Widget.extend(StandaloneFieldManagerMixin, {
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
        var $content = $(QWeb.render("ics_report_base.widgetM2MList", {field: this.field}));
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
            type: field.field_type,
            value: field.field_type == 'many2many' ? field.value : field.value && field.value[0] || false,
            domain: field.domain,
        }], options).then((recordID)=> {
            var attrs =  {
                can_create: false,
                can_write: false,
                options: {no_open: true},
            }
            if (field.field_type == 'many2many') {
                this.widget = new FieldMany2ManyTags(this, field.fieldName, this.model.get(recordID), {mode: 'edit', attrs: attrs} );
            } else {
                this.widget = new FieldMany2One(this, field.fieldName, this.model.get(recordID), {mode: 'edit', attrs: attrs} );
            }
            this._registerWidget(recordID, field.fieldName, this.widget);
        });
    },
});

export const WebReportViewAction = AbstractAction.extend({
    template: 'ics_report_base.main_view',
    templateButtons: 'ics_report_base.buttons',
    hasControlPanel: true,
    modelName: 'web.report',
    actionTitle: 'Web Report',
    events: {
        'click .ics_btn_refresh': '_onRefreshClick',
        'click .ics_expandable_row': '_onExpandableRowClick',
        'click .ics_journal_entries_row': '_onViewJournalEntriesRowClick',
        'click .ics_open_record': '_onOpenRecordClick',
        'click .sortable .ics_report_base_column_header.sortable': '_onHeaderClick',
        'click .ics_clickable_action_section': '_onSectionTitleActionClick',
        'click .ics_clickable_action_external_section': '_onSectionTitleActionExternalClick',
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
        this.report_options = this.context.options || {};
        this.report_buttons = [];
        this.report_model = this.context.model || this.modelName;
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
        this.dynamic_filters = {};
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
        this.$buttons = $(QWeb.render("ics_report_base.buttons", {report_buttons: this.report_buttons}));
        // bind actions
        _.each(this.$buttons.find('.ics_report_button'), function(el) {
            $(el).click(function() {
                self.$buttons.find('.ics_report_button').attr('disabled', true);
                var button_context = JSON.parse($(el).attr('context') || '{}');
                var button_mode = $(el).attr('mode');
                var button_action = $(el).attr('action');
                var action_method = button_mode == 'default' ? button_action : 'action_call_handler_method'
                self.report_kwargs['context']['button_context'] = button_context;
                self.report_kwargs['context']['button_action'] = button_action;
                return self._rpc({
                    model: self.report_model,
                    method: action_method,
                    args: [[self.context.report_id || false], self.report_options],
                    context: self.report_kwargs.context
                })
                .then(function(result) {
                    self.$buttons.find('.ics_report_button').attr('disabled', false);
                    if (result) {
                        var doActionProm = self.do_action(result);
                        return doActionProm;
                    }
                })
                .guardedCatch(function() {
                    self.$buttons.find('.ics_report_button').attr('disabled', false);
                });
            });
        });
        return this.$buttons;
    },
    renderSearchViewButtons: function () {
        var self = this;
        this.$searchview_buttons = $(QWeb.render("ics_report_base.searchview_buttons", {
            options: this.report_options
        }));

        if (self.report_options.filter_date) {
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
            this.$searchview_buttons.find('.ics_ar_date_filter[data-filter=' + this.report_options.filter_date_options.filter + ']').addClass('active');

            // date filter click events
            this.$searchview_buttons.find('.ics_ar_date_filter').click(function (event) {
                self.report_options.filter_date_options.filter = $(this).data('filter');
                var error = false;
                if ($(this).data('filter') === 'custom') {
                    var date_from = self.$searchview_buttons.find('.o_datepicker_input[name="date_from"]');
                    var date_to = self.$searchview_buttons.find('.o_datepicker_input[name="date_to"]');
                    if (date_from.length > 0){
                        error = date_from.val() === "" || date_to.val() === "";
                        self.report_options.filter_date_options.date_from = field_utils.parse.date(date_from.val());
                        self.report_options.filter_date_options.date_to = field_utils.parse.date(date_to.val());
                    }
                    else {
                        error = date_to.val() === "";
                        self.report_options.filter_date_options.date_to = field_utils.parse.date(date_to.val());
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
        }
        // Fold/Unfold
        this.$searchview_buttons.find('.ics_foldable_container').click(function (event) {
            event.stopPropagation();
            event.preventDefault();
            $(this).toggleClass('ics_closed_container ics_opened_container');
            self.$searchview_buttons.find('.ics_foldable_item[data-filter="'+$(this).data('filter')+'"]').toggleClass('ics_closed_container');
        });

        if (self.report_options.filter_comparison) {
            // Marking component active
            this.$searchview_buttons.find('.js_account_report_date_cmp_filter').removeClass('active');
            this.$searchview_buttons.find('.js_account_report_date_cmp_filter[data-filter=' + self.report_options.filter_comparison_options.filter + ']').addClass('active');

            // date filter click events
            this.$searchview_buttons.find('.js_account_report_date_cmp_filter').click(function (event) {
                self.report_options.filter_comparison_options.filter = $(this).data('filter');
                var number_period = $(this).parent().find('input[name="periods_number"]');
                self.report_options.filter_comparison_options.number_period = (number_period.length > 0) ? parseInt(number_period.val()) : 1;
                self.reload();
            });
        }

        if (self.report_options.filter_configuration) {
            self.$searchview_buttons.find('.ics_account_reports_filter_configuration').click(function (event) {
                self._onReportConfigurationButtonClick(event);
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
        this._render_dynamic_filters();
    },
    _render_dynamic_filters: function () {
        for (let filter_idx in this.report_options.filter_dynamic_filters || []) {
            var filter = this.report_options.filter_dynamic_filters[filter_idx];
            var filter_method = "_render_filter_" + filter.filter_type;
            // calling dynamic filter method
            if (filter_method in this) {
                this[filter_method](filter);
            } else {
                console.warn('No filter type method found ' + filter_method);
            }
        }
    },
    _render_filter_single_relation: function (filter) {
        if (!this.dynamic_filters.hasOwnProperty(filter.filter_key)) {
            this.dynamic_filters[filter.filter_key] = new FieldM2x(this, {
                label: filter.string,
                filter_key: filter.filter_key,
                modelName: filter.res_model,
                fieldName: filter.res_field,
                value: filter.res_ids.map(Number),
                domain: filter.domain || [],
                field_type: 'many2one'
            });
            this.dynamic_filters[filter.filter_key].appendTo(this.$searchview_buttons.find(`.ics_filter_key_${filter.filter_key}`));
        } else {
            this.$searchview_buttons.find(`.ics_filter_key_${filter.filter_key}`).append(this.dynamic_filters[filter.filter_key].$el);
        }
    },
    _render_filter_multi_relation: function (filter) {
        if (!this.dynamic_filters.hasOwnProperty(filter.filter_key)) {
            this.dynamic_filters[filter.filter_key] = new FieldM2x(this, {
                label: filter.string,
                filter_key: filter.filter_key,
                modelName: filter.res_model,
                fieldName: filter.res_field,
                value: filter.res_ids.map(Number),
                domain: filter.domain || [],
                field_type: 'many2many'
            });
            this.dynamic_filters[filter.filter_key].appendTo(this.$searchview_buttons.find(`.ics_filter_key_${filter.filter_key}`));
        } else {
            this.$searchview_buttons.find(`.ics_filter_key_${filter.filter_key}`).append(this.dynamic_filters[filter.filter_key].$el);
        }
    },
    _render_filter_input: function (filter) {
        var self = this;
        var $input_filter = $(QWeb.render('ics_report_base.filter_type_input', {widget: this, filter: filter}));

        $input_filter[0].addEventListener('change', function (event) {
            var new_value = $(event.target).val();
            self.report_options['dynamic_filter_search'][filter.filter_key] = new_value;
            self.reload()
        });

        this.dynamic_filters[filter.filter_key] = $input_filter;
        this.dynamic_filters[filter.filter_key].appendTo(this.$searchview_buttons.find(`.ics_filter_key_${filter.filter_key}`));
    },
    _render_filter_choice: function (filter) {
        var self = this;
        var selected_value = self.report_options['dynamic_filter_search'][filter.filter_key];
        var $input_filter = $(QWeb.render('ics_report_base.filter_type_choice', {widget: this, filter: filter, mode: 'single', active_value: selected_value}));
        this.dynamic_filters[filter.filter_key] = $input_filter;
        this.dynamic_filters[filter.filter_key].appendTo(this.$searchview_buttons.find(`.ics_filter_key_${filter.filter_key}`));
        this.$searchview_buttons.find(`.ics_filter_key_${filter.filter_key}`).find('.ics_choice_filter').on('click', function (event) {
            self.$searchview_buttons.find(`.ics_filter_key_${filter.filter_key}`).find('.ics_choice_filter').removeClass('active');
            var $el = $(event.target);
            $el.addClass('active');
            self.report_options['dynamic_filter_search'][filter.filter_key] = $el.data('choiceKey');
            self.reload();
        });
    },
    _render_filter_choice_multi: function (filter) {
        var self = this;
        var selected_values = self.report_options['dynamic_filter_search'][filter.filter_key];
        if (!_.isArray(selected_values)) {
            selected_values = [selected_values];
            self.report_options['dynamic_filter_search'][filter.filter_key] = selected_values;
        }
        var $input_filter = $(QWeb.render('ics_report_base.filter_type_choice', {widget: this, filter: filter, mode: 'multi', active_values: selected_values}));
        this.dynamic_filters[filter.filter_key] = $input_filter;
        this.dynamic_filters[filter.filter_key].appendTo(this.$searchview_buttons.find(`.ics_filter_key_${filter.filter_key}`));

        this.$searchview_buttons.find(`.ics_filter_key_${filter.filter_key}`).find('.ics_choice_filter').on('click', function (event) {
            var $el = $(event.target);
            if ($el.hasClass('active')) {
                // Deactivate
                var idx = self.report_options['dynamic_filter_search'][filter.filter_key].indexOf($el.data('choiceKey'));
                self.report_options['dynamic_filter_search'][filter.filter_key].splice(idx, 1);
                $el.removeClass('active');
            } else {
                // Activate
                $el.addClass('active');
                self.report_options['dynamic_filter_search'][filter.filter_key].push($el.data('choiceKey'));
            }
            self.reload()
        });
    },
    onFieldChance: function (widget, res_ids) {
        this.report_options['dynamic_filter_search'][widget.field.filter_key] = res_ids;
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
        this.report_kwargs['context'] = this.context;
        return this._rpc({
            model: this.modelName,  // it contains report data model
            method: 'get_web_report',
            args: [[this.context.report_id || false], this.report_options],
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
    _onRefreshClick: _.debounce(function () {
        this.reload()
    }, 500, true),
    _onHeaderClick: function (ev) {
        this.report_options.orderby = $(ev.currentTarget).children('span.label').data('expression-label');
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
    _onExpandableRowClick: _.debounce(function (event) {
        event.stopPropagation();
        event.preventDefault();
        var self = this;
        var $el = $(event.currentTarget);
        const row_key = $el.data('key');
        const section = this._findSection(this.report_data.sections, row_key);

        $el.find('.fa').toggleClass('fa-caret-right fa-caret-down');

        if ($el.hasClass('ics_section_expanded')) {
            $el.removeClass('ics_section_expanded');
            self.$el.find('.ics_child_group_lines_' + section.id).remove();
        } else {
            var ctx = _.extend(this.context, section.context || {});
            this._rpc({
                model: this.modelName,  // it contains report data model
                method: 'get_web_report_section_data',
                args: [[this.context.report_id || false], section, this.report_options],
                kwargs: this.report_kwargs,
                context: ctx
            }).then(function (lines) {
                $el.addClass('ics_section_expanded');
                if (lines.length > 0) {
                    section.children = lines;
                    var $dynamic_lines = $(QWeb.render("ics_report_base.WebReportSectionLineContainer", {
                        group_headers: self.report_options.report_header_groups, lines: lines, parent: section, headers: self.report_options.headers
                    }));
                    $dynamic_lines.addClass('ics_child_group_lines_' + section.id);
                    $dynamic_lines.insertAfter($el);
                }
            });
        }
    }, 200, true),
    _onReportConfigurationButtonClick: function (event) {
        var self = this;
        return self._rpc({
            model: self.report_model,
            method: 'action_open_report_configuration',
            args: [[this.report_options.report_id], self.report_options],
            context: self.report_kwargs.context,
        })
        .then(function(result) {
            self.do_action(result);
        });
    },
    _onViewJournalEntriesRowClick: function (event) {
        event.stopPropagation();
        event.preventDefault();
        var self = this;
        var $el = $(event.currentTarget);
        return self._rpc({
            model: self.report_model,
            method: 'action_open_moves',
            args: [[self.context.report_id || false], $el.data('key'), self.report_options],
            context: self.report_kwargs.context,
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
            args: [[self.context.report_id || false], $el.data('record-id'), self.report_options],
            context: self.report_kwargs.context,
        })
        .then(function(result){
            var doActionProm = self.do_action(result);
            return doActionProm;
        });
    },
    _onSectionTitleActionClick: function (event) {
        event.stopPropagation();
        event.preventDefault();
        var self = this;
        var $el = $(event.currentTarget);
        var row_key = $el.data('key');
        const section = this._findSection(this.report_data.sections, row_key);
        return self._rpc({
            model: 'web.report.line',
            method: 'action_redirect_to_action',
            args: [[section.report_line_id], section, self.report_options, self.report_kwargs],
            context: self.report_kwargs.context,
        })
        .then(function(result) {
            return self.do_action(result);
        });
    },
    initComponents: function () {
    }
});
