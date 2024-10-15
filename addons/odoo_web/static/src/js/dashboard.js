/** @odoo-module **/

import AbstractAction from 'web.AbstractAction';
import BasicModel from 'web.BasicModel';
import { qweb as QWeb, _t } from 'web.core';
import { useService } from "@web/core/utils/hooks";

const { Component, useState } = owl;

class MainComponent extends Component {
    setup() {
        super.setup(...arguments);
        this.rpc = useService("rpc");
        this.state = useState({});
    }
    constructor(parent, props){
        super(parent, props);
        this.parent = parent;
        this.dashboard = parent.parent;
        this.model = props.model;
        this.domain = props.domain;
        this.context = parent.context;
        this.props = props
        this.route = '/dashboard/group_by'
        this.hasGroup = true;
    }
    async willStart(...args) {
        await this.userHasGroups();
        await super.willStart(...args);
    }
    async userHasGroups() {
        if (this.props.groups) {
            this.hasGroup = await this.rpc({
                route: '/user_has_groups',
                params: {
                    groups: this.props.groups
                }
            })
        }
    }
    async getTitle () {
        if (typeof this.props.title == 'function') {
            return await this.props.title(this);
        }
        return this.props.title
    }
    getKwargs() {
        let kwargs = {};
        if (this.props.kwargs) {
            kwargs = typeof this.props.kwargs == 'function' && this.props.kwargs(this) || this.props.kwargs
        }
        kwargs['context'] = this.context;
        return kwargs
    }
    async download(ev, model, method, args){
        if (this.props.download instanceof String) {
            method = this.props.download;
        } else if (!method) {
            method = this.props.method;
        }
        if (method) {
            return this.dashboard.getSpreadSheet({
                filename: this.props.filename || await this.getTitle() || 'data',
                model: model || this.model || this.props.modelName,
                method: method,
                args: args || [this.getDomain()],
                kwargs: {
                    limit: this.props.maxDownloadLimit,
                    offset: 0,
                    ...this.getKwargs(),
                    context: {...this.context, 'download': true}
                }
            });
        }
        return this.dashboard.getSpreadSheet({
            filename: this.props.filename || await this.getTitle() || 'data',
            model: model || this.model || this.props.modelName,
            route: this.route,
            kwargs: {
                model: model || this.model || this.props.modelName,
                domain: this.getDomain(),
                group_by: this.props.groupBy,
                labelField: this.props.labelField,
                dataField: this.props.dataField,
                limit: this.props.maxDownloadLimit,
                offset: 0,
                ...this.getKwargs(),
                method: this.props.method,
                dataFields: this.props.dataFields,
                context: {...this.context, 'download': true}
            }
        });
    }
    getDomain() {
        if (this.props.domain) {
            return this.domain.concat(this.props.domain)
        }
        return this.domain || []
    }
}

const Dashboard = AbstractAction.extend({
    template: 'odoo_web.dashboard',
    templateButtons: 'odoo_web.dashboard.buttons',
    templateComponent: false,
    hasControlPanel: true,
    withSearchBar: true,
    loadControlPanel: true,
    modelName: false,
    dashboardTitle: 'Dashboard',
    searchMenuTypes: ['filter', 'favorite'],
    custom_events: _.extend({}, AbstractAction.prototype.custom_events, {
        search: '_onSearch'
    }),
    config: _.extend({}, AbstractAction.prototype.config, {
        Model: BasicModel,
    }),
    button_events: {
        'click .fa-refresh': '_onRefreshClick',
        'click .fa-download': '_onDownloadClick'
    },
    init: function (parent, action, options) {
        this._super.apply(this, arguments);

        this.action = action;
        this.context = action.context;
        this.action_manager = parent;
        this.domain = [];
        this.options = options || {};
        this.searchModelConfig.modelName = this.modelName;
        this.controlPanelProps.cp_content = {};
        this.env = parent.env;
        this.widget = false;
        this.ActiveWidget = false
        this.__owl__ = {
            children: {},
        }
        this.model = new this.config.Model(this, {
            modelName: this.modelName,
        });
    },
    reload: async function() {
        this.destoryComponent();
        this.initComponent();
    },
    loadViews: function (modelName, context, views, options={}) {
        if (!options.action_id) {
            options.action_id = this.action.id;
        }
        return this._super.call(this, modelName, context, views, options);
    },
    start: function () {
        return this._super.apply(this, arguments)
        .then(() => { this.domain = this.searchModel._getQuery().domain; })
        .then(this._updateControlPanel.bind(this))
        .then(this.destoryComponent.bind(this))
        .then(this.initComponent.bind(this));
    },
    initComponent: function () {
        if (this.component || this.templateComponent) {
            this.widget = this.getComponent();
            this.widget.mount(this.$el[0]);
        }
    },
    destoryComponent: function () {
        if (this.widget) {
            this.widget.destroy();
            this.widget = false;
        }
    },
    getComponentProps: function () {
        return {};
    },
    getComponent: function () {
        const props = { model: this.modelName, domain: this.domain, ...this.getComponentProps() };
        if (this.component) {
            return new this.component(this, props);
        }
        class component extends MainComponent {}
        component.template = this.templateComponent;
        return new component(this, props);
    },
    _onSearch: function (searchQuery) {
        this.domain = searchQuery.domain;
        this.model.display_context = 'search';
        this.reload();
    },
    getDomain: function () {
        return this.domain || [];
    },
    getSpreadSheet: function (data) {
        this.getSession().get_file({
            url: '/odoo_web/export/xlsx',
            data: {
                data:JSON.stringify(data)
            },
            error: (error) => this.call('crash_manager', 'rpc_error', error),
        });
    },
    _getStatusConfig: function () {
        return {
            title: this.dashboardTitle,
            cp_content: {$buttons: this.$buttons},
        };
    },
    _updateControlPanel: function () {
        this.$buttons = $(QWeb.render(this.templateButtons, {widget: this}));
        for (let key in this.button_events) {
            let [ev, target] = key.split(' ');
            this.$buttons.on(ev, target, this[this.button_events[key]].bind(this));
        }
        var status = this._getStatusConfig();
        this.updateControlPanel(status);
    },
    _onRefreshClick: function () {
        return this.reload();
    },
    _onDownloadClick: async function () {
        let resIDs = await this.getRecordIds();
        let fields = await this.getAllFields();

        this.getSpreadSheet({
            model: this.modelName,
            fields: fields,
            ids: resIDs.map((e) => e.id),
            domain: this.getDomain(),
            import_compat: false,
            context: this.context,
        })
    },
    getRecordIds: async function() {
        return await this._rpc({
            model: this.modelName,
            method: 'search_read',
            domain: this.getDomain(),
            fields: ['id'],
        });
    },
    getAllFields: async function() {
        let exportFields = this.getExportFields();
        let fields = await this._rpc({
            route: '/web/export/get_fields',
            params: {
                model: this.modelName,
                context: this.context,
            },
        });

        if (exportFields.length) {
            fields = fields.filter(element => exportFields.includes(element.id));
            fields = fields.sort((x, y) => {
                return exportFields.indexOf(x.id) - exportFields.indexOf(y.id);
            });
        }
        fields.forEach(element => {
            element.name = element.id;
            element.label = element.string;
        });
        return fields;
    },
    getExportFields: function () {
        return [];
    }
});

export {
    Dashboard,
    MainComponent
}
