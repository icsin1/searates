/** @odoo-module **/

import { action_registry } from 'web.core';
import { WebReportViewAction } from '@ics_report_base/js/web_report_action';
import { WebReportSection } from '@ics_report_base/js/web_report_section';


export const WebReportView = WebReportViewAction.extend({
    initComponents: function () {
        this._super.apply(this, arguments);
        let component = new WebReportSection(this, {data: this.report_data});
        this.widgets.push(component);
        component.mount(this.$el.find('.ics_report_base')[0]);
    }
});

action_registry.add('ics_report_base.web_report', WebReportView);
