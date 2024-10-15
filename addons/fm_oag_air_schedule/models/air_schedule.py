from odoo import models, fields, api, _


class FreightAirSchedule(models.Model):
    _inherit = 'freight.air.schedule'

    source = fields.Selection(
        selection_add=[("oag", "OAG")],
        ondelete={'oag': 'set default'}
    )

    @api.model
    def action_oag_search_wizard(self):
        ctx = {
            'default_source': self.env.context.get('default_source'),
            'default_transport_mode_id': self.env.context.get('default_transport_mode_id')
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
