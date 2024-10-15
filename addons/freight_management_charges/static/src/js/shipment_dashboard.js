/** @odoo-module **/

import { action_registry } from 'web.core';
import { Dashboard } from '@odoo_web/js/dashboard';
import session from 'web.session';

export const ShipmentDashboard = Dashboard.extend({
    modelName: 'freight.house.shipment',
    dashboardTitle: 'Shipments',
    templateComponent: 'dashboard.shipment',
    getVolumeUoMTitle: async function(){
        let UoMName =  await this._rpc({
            model: "res.company",
            method: 'search_read',
            domain: [['id', '=', parseInt(session.company_id)]],
            fields: ['volume_uom_id'],
            args: [],
            limit: 1,
        });
        return 'Total Volume in ' + (UoMName && UoMName[0].volume_uom_id[1] || 'm3');
    }
});

action_registry.add('fm_shipment_dashboard', ShipmentDashboard);
