/** @odoo-module **/

const ControlPanel = require('web.ControlPanel');
import { patch } from 'web.utils';
import { session } from '@web/session';


patch(ControlPanel.prototype, 'ControlPanel', {
    async willStart(){
        const prom = this._super.apply(this, arguments);
        return Promise.all([prom, this.loadData()])
    },
    async loadData() {
        if (this.env.action) {
            let res = await this.rpc({
                model: 'res.company',
                method: 'read',
                args: [session.company_id, ['view_customization']]
            })
            res = res && res[0] || {};
            if (res.view_customization == 'all') {
                this.props.has_view_customize_access = true
            } else {
                this.props.has_view_customize_access = session.is_admin;
            }
        }
    }
})
