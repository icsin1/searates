from odoo import models,_


class AuditLogOperation(models.Model):
    _inherit = 'ir.audit.log.operation'

    def button_open_chatter_view(self):
        return {
            'name': _('Audit Trail'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.res_id
        }
