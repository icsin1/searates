from odoo import models, fields


class AirScheduleSelectorWizard(models.TransientModel):
    _inherit = 'air.schedule.selector.wizard'

    master_shipment_id = fields.Many2one('freight.master.shipment')
    house_shipment_id = fields.Many2one('freight.house.shipment')
