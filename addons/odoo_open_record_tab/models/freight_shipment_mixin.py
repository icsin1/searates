# -*- coding: utf-8 -*-

from odoo import models


class FreightShipmentMixin(models.AbstractModel):
    _inherit = 'freight.shipment.mixin'

    def action_open_on_new_tab(self):
        self.ensure_one()
        context = self.env.context
        params = context.get('params', {'action': context.get('action')})
        return {
            'type': 'ir.actions.act_url',
            'target': '_blank',
            'url': "/web#id=%(id)s&action=%(action)s&model=%(model)s&view_type=%(view_type)s&menu_id=%(menu_id)s&active_id=%(active_id)s" % {
                'id': self.id,
                'model': self._name,
                'view_type': 'form',
                'menu_id': params.get('menu_id'),
                'action': params.get('action'),
                'active_id': params.get('active_id')
            },
        }
