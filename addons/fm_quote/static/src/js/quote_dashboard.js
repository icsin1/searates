/** @odoo-module **/

import { action_registry } from 'web.core';
import { Dashboard } from '@odoo_web/js/dashboard';

export const QuoteDashboard = Dashboard.extend({
    modelName: 'shipment.quote',
    dashboardTitle: 'Quotes',
    templateComponent: 'dashboard.quote',

    getDomain: function () {
        let domain = this._super.apply(this, arguments);
        if (domain) {
            return domain.concat([['state', '!=', 'cancel']]);
        }
        return domain;
    },
    getExportFields: function () {
        return [
            'name', 'client_id', 'transport_mode_id', 'shipment_type_id',
            'cargo_type_id', 'service_mode_id', 'incoterm_id', 'state', 'origin_country_id',
            'destination_country_id', 'estimated_total_revenue', 'estimated_total_cost', 'estimated_profit'
        ]
    }
});

action_registry.add('fm_quote_dashboard', QuoteDashboard);
