from odoo import models, fields


class SailingScheduleSelectorWizard(models.TransientModel):
    _inherit = 'sailing.schedule.selector.wizard'

    master_shipment_id = fields.Many2one('freight.master.shipment')
    house_shipment_id = fields.Many2one('freight.house.shipment')
