/** @odoo-module **/

import { action_registry } from 'web.core';
import { Dashboard } from '@odoo_web/js/dashboard';

export const SalesCRMDashboard = Dashboard.extend({
    modelName: 'crm.sale.target.line',
    dashboardTitle: 'Target vs Actual',
    templateComponent: 'dashboard.fm_sale_crm',
});

action_registry.add('fm_sales_and_crm_dashboard', SalesCRMDashboard);
