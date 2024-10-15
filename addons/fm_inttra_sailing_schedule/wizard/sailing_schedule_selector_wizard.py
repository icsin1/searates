from odoo import models, _


class SailingScheduleSelectorWizard(models.TransientModel):
    _inherit = 'sailing.schedule.selector.wizard'

    def action_import_schedule(self):
        ctx = {
            'open_selector_wizard': self.id,
            'selector_wizard_context': self.env.context,
            'default_origin_port_id': self.origin_port_id.id,
            'default_destination_port_id': self.destination_port_id.id,
            'default_source': 'inttra',
            'default_transport_mode_id': self.env.ref('freight_base.transport_mode_sea').id
        }
        return {
            'name': _('Import Sailing Schedule'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'inttra.schedule.search.wizard',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
