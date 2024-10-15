# -*- coding: utf-8 -*-

from odoo import models


class FreightChargeMixin(models.AbstractModel):
    _inherit = 'mixin.freight.charge'

    def action_open_on_new_tab(self):
        self.ensure_one()
        context = self.env.context
        params = context.get('params', {'action': context.get('action')})
        return {
            'type': 'ir.actions.act_url',
            'target': '_blank',
            'url': "/web#id=%(id)s&menu_id=%(menu_id)s&model=%(model)s&view_type=form" % {
                'id': self.id,
                'model': self._name,
                'menu_id': params.get('menu_id'),
            },
        }
