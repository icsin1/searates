/** @odoo-module **/

import { action_registry } from 'web.core';
import { AccountingReportView } from '@ics_account_reports/js/account_report';
import { AccountReportSection } from '@ics_account_reports/js/account_report_section';


export const FinanceReportView = AccountingReportView.extend({
    initComponents: function () {
        this._super.apply(this, arguments);
        let component = new AccountReportSection(this, {data: this.report_data});
        this.widgets.push(component);
        component.mount(this.$el.find('.ics_account_report')[0]);
    }
});

action_registry.add('ics_account_reports.finance_reports', FinanceReportView);
