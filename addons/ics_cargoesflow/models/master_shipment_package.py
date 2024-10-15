from odoo import models, _


class FreightMasterShipmentPackageMixin(models.Model):
    _inherit = 'freight.master.shipment.package'

    def action_shipment_milestone_container(self):
        milestone_ids = self.env['freight.master.shipment.event'].search([
            ('shipment_id', '=', self.shipment_id.id),
            ('container_id', '=', self.container_number.id)
        ])
        return {
            'name': _('Milestones Tracking'),
            'res_model': 'freight.master.shipment.event',
            'views': [(False, 'tree')],
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': {'create': False, 'edit': False},
            'domain': [('id', 'in', milestone_ids.ids)]
        }
