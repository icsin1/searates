
from odoo import models, fields


class INTTRAScheduleSearchWizard(models.TransientModel):
    _inherit = 'inttra.schedule.search.wizard'

    shipment_quote_id = fields.Many2one('shipment.quote')

    def action_import_schedules(self):
        res = super().action_import_schedules()
        if self.shipment_quote_id and res:
            self.shipment_quote_id.write({'schedule_ids': [(4, each_rec.id) for each_rec in res]})
        return res
