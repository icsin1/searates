from odoo import models, fields, api, _


class FreightSailingSchedule(models.Model):
    _inherit = 'freight.schedule'

    source = fields.Selection(
        selection_add=[("inttra", "Imported")],
        ondelete={'inttra': 'set default'}
    )

    @api.model
    def action_inttra_search_wizard(self):
        ctx = {
            'default_source': self.env.context.get('default_source'),
            'default_transport_mode_id': self.env.context.get('default_transport_mode_id')
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
