from odoo import models, _


class HouseShipmentPackageMixin(models.Model):
    _inherit = 'freight.house.shipment.package'

    def action_shipment_milestone_container(self):
        milestone_ids = self.env['freight.house.shipment.event'].search([
            ('shipment_id', '=', self.shipment_id.id),
            ('container_id', '=', self.container_number.id)
        ])
        return {
            'name': _('Milestones Tracking'),
            'res_model': 'freight.house.shipment.event',
            'views': [(False, 'tree')],
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': {'create': False, 'edit': False},
            'domain': [('id', 'in', milestone_ids.ids)]
        }
