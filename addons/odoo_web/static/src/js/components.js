/** @odoo-module **/

import { MainComponent } from '@odoo_web/js/dashboard';
import { useAssets } from "@web/core/assets";
import { useEffect } from "@web/core/utils/hooks";


const { useState } = owl;
const { useRef } = owl.hooks;

export class GraphView extends MainComponent {
    static template = 'GraphView'
    setup() {
        this.model = this.props.model;

        this.canvasRef = useRef("canvas");
        this.containerRef = useRef("container");

        this.chart = null;
        this.tooltip = null;
        this.legendTooltip = null;

        useAssets({ jsLibs: ['/web/static/lib/Chart/Chart.js'] });
    }
    constructor(parent, props) {
        super(parent, props);
        this.model = props.modelName || parent.model;
        this.domain = parent.domain;
        this.parent = parent;
        this.filter = props.filter;
        this.selectedDataField = props.selectedDataField || props.dataField;
        this.length = props.limit || 0;
        this.allType = [ 'line', 'bar', 'horizontalBar', 'radar', 'pie', 'doughnut', 'polarArea', 'bubble', 'scatter', 'table'];

        if (!props.type) {
            props.type = ['table'];
        }
        this.type = props.type[0];
        if (!props.limit && this.type != 'table') {
            this.limit = 10;
        } else {
            if (props.limitOptions && props.limitOptions.length) {
                this.limit = props.limitOptions[0];
            } else {
                this.limit = props.limit || 5
            }
        }
        this.state = useState({
            'tableData': [],
            'labels': [],
            'title': typeof this.props.title  == 'function' ? '' : this.props.title,
            'offset': 0,
            'length': this.length,
            'limit': this.limit,
            'filter': this.filter,
            'selectedDataField': this.selectedDataField,
            'type': props.type[0],
            'loaded': false,
        });
        this.getNext = this.getNextType();
    }
    getNextType() {
        let index = 1;
        let type = this.props.type;

        return function () {
            let value = type[index];
            index = (index + 1) % type.length;
            return value;
        }
    }
    getIcon(type) {
        switch (type) {
            case 'table':
                return 'fa fa-list';
            case 'bar':
                return 'fa fa-bar-chart';
            case 'line':
                return 'fa-line-chart';
            case'bar':
                return 'fa fa-bar-chart';
            case'horizontalBar':
                return 'fa fa-bar-chart';
            case'radar':
                return 'fa fa-area-chart';
            case'pie':
                return 'fa fa-pie-chart';
            case'doughnut':
                return 'fa fa-circle-o-notch';
            case'polarArea':
                return 'fa fa-area-chart';
            case'bubble':
                return 'fa fa-area-chart';
            case'scatter':
                return 'fa fa-area-chart';
            default:
                return 'fa fa-download';
        }
    }
    async changeType(type) {
        this.state.type = type;
        this.loadData().then(() => {
            this.state.loaded = true;
        });
    }
    async getConfig(type) {
        var self = this;
        var count = 0;
        return {
            type: type,
            data: await this.getData(),
            options: {
                maintainAspectRatio: true,
                scales: this.getScales(),
                responsive: true,
                legend: {
                    display: this.props.multi,
                    position: 'right',
                    align: 'start',
                    labels: {
                        fontSize: 10,
                        boxWidth: 10,
                        usePointStyle: true,
                        padding: 5,
                        filter: function(legendItem, chartData) {
                            count++;
                            return count <= 10;
                        },

                    }
                },
                legendCallback: function(chart) {
                    var text = [];
                    text.push('<ul class="' + chart.id + '-legend">');
                    for (var i = 0; i < chart.data.labels.length; i++) {
                        text.push('<li><div class="legendValue"><span class="color" style="background-color:' + chart.data.datasets[0].backgroundColor[i] + '"></span>');
                        text.push('<span class="label">' + chart.data.labels[i] + '</span>');
                        text.push('</div></li><div class="clear"></div>');
                    }
                    text.push('</ul>');
                    return text.join('');
                },
                tooltips: {
                    enabled: true
                },
                onClick: async function(event, elements) {
                    if (elements.length > 0) {
                        let record = self.state.tableData[elements[0]._index];

                        if (record) {
                            self.dashboard.do_action({
                                name: `${ await self.getTitle() } (${record[self.props.labelField]})`,
                                type: 'ir.actions.act_window',
                                res_model: self.props.modelName || self.model,
                                domain: record.__domain,
                                views: [[false, 'list'], [false, 'form']],
                                view_mode: 'list,form',
                                target: 'current',
                            })
                        }
                    }
                }
            }
        }
    }
    getScales() {
        if (['pie', 'doughnut'].includes(this.state.type)) {
            return {}
        }
        return {
            yAxes: [{
                ticks: {
                    stepSize: this.props.multi ? false : 5,
                    beginAtZero: true,
                },
            }],
            xAxes: [{
                ticks: {
                    stepSize: this.props.multi ? false : 5,
                    beginAtZero: true,
                },
            }],
        }
    }
    async getData() {
        if (this.props.multi && this.state.type != 'table') {
            if (!(this.state.tableData && this.state.tableData.labels)) {
                return {}
            }
            return {
                'labels': [...this.state.tableData.labels],
                'datasets': this.state.tableData.datasets.map(e => {
                    let data = {}
                    for (let key in e) {
                        if (e[key] instanceof Array) {
                            data[key] = [...e[key]]
                            continue
                        }
                        data[key] = e[key]
                    }
                    return data
                })

            }
        }
        return {
            labels: this.state.tableData.map(e => e[this.props.labelField]),
            datasets: [{
                label: await this.getTitle(),
                data: this.state.tableData.map(e => e[this.state.selectedDataField]),
                backgroundColor: this.getColors(),
                borderWidth: 2
            }]
        }
    }
    async renderChart() {
        if (this.state.type == 'table') {
            return
        }
        var ctx = this.el.querySelector('canvas').getContext('2d');
        let chart = new Chart(ctx, await this.getConfig(this.state.type));
        if (this.chart) {
            this.chart.destroy();
        }
        this.chart = chart;
        Chart.animationService.advance();
        if (!this.props.multi) {
            this.el.querySelector('#legend').innerHTML = chart.generateLegend();
        }

        this.chart.resize = function () {
            try { return this.chart.resize.call(this.chart); }
            catch (err) {}
        }
    }
    async loadData() {
        if (!this.hasGroup) {
            return
        }
        if (this.props.data) {
            this.state.tableData = this.props.data;
            this.state.length = this.props.data.length;
            this.state.title = await this.getTitle();
            return
        }
        let limit = this.state.type == 'table' || (this.props.limitOptions && this.props.limitOptions.length) ? this.state.limit : undefined;
        let tableData = false;
        let tableDataAll = false
        let tableDataAllLength = false

        if (this.props.groupBy) {
            tableData = await this.rpc({
                route: this.route,
                params: {
                    'model': this.model,
                    'domain': this.getDomain(),
                    'group_by': this.props.groupBy,
                    'labelField': this.props.labelField,
                    'dataField': this.props.dataField,
                    'limit': limit,
                    'offset': this.state.offset,
                    'context': this.context,
                    'sort': typeof this.props.sort == 'undefined' || this.props.sort,
                    'method': this.props.method,
                    'dataFields': this.props.dataFields,
                }
            })
            tableDataAllLength = await this.rpc({
                route: this.route,
                params: {
                    'model': this.model,
                    'domain': this.getDomain(),
                    'group_by': this.props.groupBy,
                    'labelField': this.props.labelField,
                    'dataField': this.props.dataField,
                    'limit': this.props.maxLimit,
                    'offset': 0,
                    'context': this.context,
                    'sort': typeof this.props.sort == 'undefined' || this.props.sort,
                    'method': this.props.method,
                    'dataFields': this.props.dataFields,
                    'count': true
                }
            })
        } else {
            tableData = await this.rpc({
                model: this.model,
                method: this.props.method,
                args: [this.getDomain(), limit, this.state.offset],
                kwargs: this.getKwargs()
            });
            tableDataAll = await this.rpc({
                model: this.model,
                method: this.props.method,
                args: [this.getDomain(), this.props.maxLimit],
                kwargs: {...this.getKwargs(), count: true}
            });
            tableDataAllLength = typeof tableDataAll == 'number' ? tableDataAll: tableDataAll.length
        }
        let labels = {};
        if (tableData.length) {
            let firstLine = tableData[0];
            for (let key in firstLine) {
                if (!key.startsWith("__")) {
                    labels[key] = firstLine[key]
                }
            }
        }
        this.state.tableData = tableData;
        this.state.labels = labels;
        this.state.length = tableDataAllLength;
        this.state.title = await this.getTitle();
    }
    async willStart(...args) {
        await super.willStart(...args);
        this.loadData().then(() => {
            this.state.loaded = true;
        });
    }
    async render (...args) {
        if (this.state.type == 'table') {
            if (this.chart) {
                this.chart.destroy();
            }
        }
        let res = await super.render(...args);
        await this.renderChart();
        return res;
    }
    getColors() {
        let defaultColors = [
            '#36A2EB',
            '#F56182',
            '#4BC0C0',
            '#FA9E3F',
            '#9B76FC',
            '#FFCD56',
            '#C9CBCF',
        ];
        if (this.state.tableData.length > 7) {
            return defaultColors.concat(this.generateColors(this.state.tableData.length));
        }
        return defaultColors;
    }
    generateColor() {
        var letters = '0123456789ABCDEF';
        var color = '#';
        for (var i = 0; i < 6; i++) {
          color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    }
    generateColors(numColors) {
        var colors = [];
        for (var i = 0; i < numColors; i++) {
            colors.push(this.generateColor());
        }
        return colors;
    }
    nextPage() {
        this.state.loaded = false;
        let diff = Math.max(this.state.limit - this.state.offset, 0);
        this.state.offset += diff;
        this.state.limit += diff;
        this.loadData().then(() => {
            this.state.loaded = true;
        });
    }
    previousPage() {
        this.state.loaded = false;
        let diff = Math.max(this.state.limit - this.state.offset, 0);
        this.state.offset = Math.max(this.state.offset - diff, 0);
        this.state.limit = Math.max(this.state.limit - diff, this.limit);
        this.loadData().then(() => {
            this.state.loaded = true;
        });
    }
    onLimitChange(ev) {
        this.state.loaded = false;
        this.state.offset = 0;
        this.state.limit = +ev.target.selectedOptions[0].value
        this.loadData().then(() => {
            this.state.loaded = true;
        });
    }
    onDataFieldChange(ev) {
        this.state.selectedDataField = ev.target.selectedOptions[0].innerHTML
    }
    onFilterChange(ev) {
        this.state.loaded = false;
        this.state.filter = ev.target.selectedOptions[0].value;
        this.state.offset = 0;
        this.state.length = this.length;
        this.state.limit = this.limit;
        this.loadData().then(() => {
            this.state.loaded = true;
        });
    }
}

class RecordView extends MainComponent {
    static template = 'RecordView'

    constructor(parent, props) {
        super(parent, props);
        this.model = props.modelName || parent.model;
        this.domain = parent.domain;
        this.method = parent.method;
        this.state = useState({
            'count': 0,
            'title': typeof this.props.title  == 'function' ? '' : this.props.title,
            'loaded': false
        });
    }
    async willStart(...args) {
        await super.willStart(...args);
        this.loadData(...args).then(() => {
            this.state.loaded = true;
        });
    }
    async loadData(...args) {
        if (!this.hasGroup) {
            return
        }

        let method = 'search_count'
        if (this.props.method) {
            method = this.props.method
        }
        let count = 0;
        if (this.props.groupBy) {
            let tableDataAllLength = await this.rpc({
                route: this.route,
                params: {
                    'model': this.model,
                    'domain': this.getDomain(),
                    'group_by': this.props.groupBy,
                    'context': this.context,
                    'limit': this.props.maxLimit,
                    'method': this.props.method,
                    'count': true
                }
            })
            count = tableDataAllLength;
        } else {
            count = await this.rpc({
                model: this.model,
                method: method,
                args: [this.getDomain()],
            });
        }
        this.state.count = count;
        this.state.title = await this.getTitle();
    }
}

MainComponent.template = 'fm_dashboard.main';
MainComponent.components = { RecordView, GraphView };
