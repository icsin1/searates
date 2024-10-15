from odoo import models, _


class AirScheduleSelectorWizard(models.TransientModel):
    _inherit = 'air.schedule.selector.wizard'

    def action_import_schedule(self):
        ctx = {
            'open_selector_wizard': self.id,
            'selector_wizard_context': self.env.context,
            'default_origin_port_id': self.origin_port_id.id,
            'default_destination_port_id': self.destination_port_id.id,
            'default_source': 'oag',
            'default_transport_mode_id': self.env.ref('freight_base.transport_mode_air').id
        }
        return {
            'name': _('Import Air Schedule'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'oag.schedule.search.wizard',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
