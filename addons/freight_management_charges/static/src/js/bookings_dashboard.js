/** @odoo-module **/

import { action_registry } from 'web.core';
import { Dashboard } from '@odoo_web/js/dashboard';

export const BookingsDashboard = Dashboard.extend({
    modelName: 'freight.master.shipment',
    dashboardTitle: 'Carrier Bookings',
    templateComponent: 'dashboard.bookings',
});

action_registry.add('fm_bookings_dashboard', BookingsDashboard);
